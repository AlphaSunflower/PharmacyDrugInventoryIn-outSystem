package com.gcky.durginoutsystem.service.impl;

import java.math.BigDecimal; // Import added
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.entity.InventoryCheckDetail;
import com.gcky.durginoutsystem.entity.InventoryCheckTask;
import com.gcky.durginoutsystem.exception.BusinessException;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckDetailMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckTaskMapper;
import com.gcky.durginoutsystem.service.DrugStockService;
import com.gcky.durginoutsystem.service.InventoryService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class InventoryServiceImpl implements InventoryService {

    @Autowired
    private InventoryCheckTaskMapper taskMapper;
    @Autowired
    private InventoryCheckDetailMapper detailMapper;
    @Autowired
    private DrugMapper drugMapper;
    @Autowired
    private DrugBatchMapper drugBatchMapper;
    @Autowired
    private DrugStockService drugStockService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long generateTask(String month) {
        // 1. 检查该月任务是否已存在
        QueryWrapper<InventoryCheckTask> wrapper = new QueryWrapper<>();
        wrapper.eq("month", month);
        InventoryCheckTask exist = taskMapper.selectOne(wrapper);
        if (exist != null) {
            return exist.getId();
        }

        // 2. 创建新任务
        InventoryCheckTask task = new InventoryCheckTask();
        task.setMonth(month);
        task.setStatus("PENDING");
        task.setCreatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        // 3. 生成快照明细 (快照当前系统库存)
        List<Drug> drugs = drugMapper.selectList(new QueryWrapper<Drug>().eq("is_deleted", 0));
        for (Drug drug : drugs) {
            InventoryCheckDetail detail = new InventoryCheckDetail();
            detail.setTaskId(task.getId());
            detail.setDrugId(drug.getId());
            detail.setSystemStock(drug.getStockQuantity());
            detail.setActualStock(null); // 待填
            detail.setDiscrepancy(null);
            detailMapper.insert(detail);
        }

        return task.getId();
    }

    @Override
    public List<Map<String, Object>> getTaskDetails(Long taskId) {
        QueryWrapper<InventoryCheckDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("task_id", taskId);
        List<InventoryCheckDetail> details = detailMapper.selectList(wrapper);

        // 批量加载药品信息（消除 N+1）
        List<Long> drugIds = details.stream().map(InventoryCheckDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        return details.stream().map(d -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", d.getId());
            map.put("taskId", d.getTaskId());
            map.put("drugId", d.getDrugId());
            map.put("systemStock", d.getSystemStock());
            map.put("actualStock", d.getActualStock());
            map.put("discrepancy", d.getDiscrepancy());
            map.put("remark", d.getRemark());
            Drug drug = drugMap.get(d.getDrugId());
            map.put("drugName", drug != null ? drug.getName() : "Unknown");
            map.put("drugSpec", drug != null ? drug.getSpec() : "");
            return map;
        }).collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateDetail(Long detailId, Integer actualStock, String remark) {
        InventoryCheckDetail detail = detailMapper.selectById(detailId);
        if (detail == null) return;
        
        detail.setActualStock(actualStock);
        detail.setRemark(remark);
        // 计算差异 = 实盘 - 账面
        if (actualStock != null) {
            detail.setDiscrepancy(actualStock - detail.getSystemStock());
        } else {
            detail.setDiscrepancy(null);
        }
        
        // 计算实盘金额 (基于 FIFO 逻辑预估)
        // 注意：这里只是预估价值，不代表真实扣减。逻辑是：假设当前库存就是这 actualStock 个，它们的值是多少？
        // 我们从最早的批次开始凑，直到凑够 actualStock
        BigDecimal actualAmount = calculateInventoryValue(detail.getDrugId(), actualStock);
        detail.setActualAmount(actualAmount);
        
        detailMapper.updateById(detail);
    }

    /**
     * 计算指定数量的药品库存价值 (FIFO)
     */
    private BigDecimal calculateInventoryValue(Long drugId, Integer quantity) {
        if (quantity == null || quantity <= 0) return BigDecimal.ZERO;

        QueryWrapper<DrugBatch> query = new QueryWrapper<>();
        query.eq("drug_id", drugId)
             .gt("stock_quantity", 0)
             .orderByAsc("created_at");
        List<DrugBatch> batches = drugBatchMapper.selectList(query);
        
        BigDecimal totalValue = BigDecimal.ZERO;
        int remaining = quantity;
        
        // 1. 先用现有批次凑
        for (DrugBatch batch : batches) {
            if (remaining <= 0) break;
            int take = Math.min(remaining, batch.getStockQuantity()); // 注意：这里不是扣减，只是计算价值，所以取 batch.getStockQuantity() 即可
            // 但如果实盘数量 > 系统库存，这里可能会有问题，因为批次加起来不够
            // 所以我们假设：
            // 如果实盘 <= 系统库存：按 FIFO 取批次价格
            // 如果实盘 > 系统库存：先按 FIFO 取完所有批次，多出来的部分按最新进价（或参考价）计算
            
            totalValue = totalValue.add(batch.getPrice().multiply(new BigDecimal(take)));
            remaining -= take;
        }
        
        // 2. 如果还有剩余 (说明盘盈了，或者批次库存和总库存不一致)，多出来的部分按参考价计算
        if (remaining > 0) {
            Drug drug = drugMapper.selectById(drugId);
            BigDecimal refPrice = drug != null ? drug.getPrice() : BigDecimal.ZERO;
            totalValue = totalValue.add(refPrice.multiply(new BigDecimal(remaining)));
        }
        
        return totalValue;
    }



    @Override
    @Transactional(rollbackFor = Exception.class)
    public void completeTask(Long taskId) {
        // 0. 校验任务存在且未完成
        InventoryCheckTask existing = taskMapper.selectById(taskId);
        if (existing == null) {
            throw new BusinessException("盘点任务不存在");
        }
        if ("COMPLETED".equals(existing.getStatus())) {
            throw new BusinessException("盘点任务已完成，无需重复提交");
        }

        // 1. 检查是否所有项都已正确填写实盘数量
        QueryWrapper<InventoryCheckDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("task_id", taskId);
        wrapper.and(w -> w.isNull("actual_stock").or().lt("actual_stock", 0));
        if (detailMapper.selectCount(wrapper) > 0) {
            throw new BusinessException("还有药品未正确填写实盘数量，无法提交任务");
        }

        // 2. 更新任务状态
        InventoryCheckTask task = new InventoryCheckTask();
        task.setId(taskId);
        task.setStatus("COMPLETED");
        task.setCompletedAt(LocalDateTime.now());
        taskMapper.updateById(task);

        // 2. 更新药品系统库存
        QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
        detailWrapper.eq("task_id", taskId);
        List<InventoryCheckDetail> details = detailMapper.selectList(detailWrapper);

        // Batch-load all referenced drugs (eliminate N+1)
        List<Long> drugIds = details.stream().map(InventoryCheckDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        for (InventoryCheckDetail detail : details) {
            if (detail.getActualStock() != null) {
                Drug drug = drugMap.get(detail.getDrugId());
                if (drug != null) {
                    int diff = detail.getActualStock() - drug.getStockQuantity();

                    if (diff != 0) {
                        adjustBatches(drug.getId(), diff);
                    }

                    drugStockService.updateDrugTotalStock(drug.getId());
                }
            }
        }
    }

    /**
     * 自动调整批次库存以匹配总库存变化
     * 策略：
     * - 盘盈 (diff > 0): 增加到最新批次 (或创建新批次)
     * - 盘亏 (diff < 0): 优先扣减最早批次 (FIFO)
     */
        /**
     * Atomically adjust batch stock to match target actual stock.
     * Computes diff inside FOR UPDATE lock scope, then applies adjustment,
     * then recalculates total drug stock — all under batch-level row locks.
     */
    private void adjustBatchesWithDiff(Long drugId, int actualStock) {
        // Acquire row-level locks on all batches for this drug
        List<DrugBatch> batches = drugBatchMapper.selectBatchesForUpdate(drugId);

        // Compute current total from locked batches
        int currentTotal = batches.stream().mapToInt(DrugBatch::getStockQuantity).sum();
        int diff = actualStock - currentTotal;

        if (diff > 0) {
            // Surplus: add to latest batch
            DrugBatch latestBatch = drugBatchMapper.selectLatestForUpdate(drugId);
            if (latestBatch != null) {
                drugBatchMapper.incrementStock(latestBatch.getId(), diff);
            } else {
                Drug drug = drugMapper.selectById(drugId);
                DrugBatch newBatch = new DrugBatch();
                newBatch.setDrugId(drugId);
                newBatch.setPrice(drug != null ? drug.getPrice() : BigDecimal.ZERO);
                newBatch.setStockQuantity(diff);
                newBatch.setInitialQuantity(diff);
                newBatch.setCreatedAt(LocalDateTime.now());
                newBatch.setBatchNo("INV_CHECK_AUTO");
                drugBatchMapper.insert(newBatch);
            }
        } else if (diff < 0) {
            // Shortage: FIFO deduction
            int toDeduct = Math.abs(diff);

            for (DrugBatch batch : batches) {
                if (toDeduct <= 0) break;
                int deductAmount = Math.min(batch.getStockQuantity(), toDeduct);
                drugBatchMapper.incrementStock(batch.getId(), -deductAmount);
                toDeduct -= deductAmount;
            }
        }

        // Recalculate total drug stock from batch sums
        drugStockService.updateDrugTotalStock(drugId);
    }

    private void adjustBatches(Long drugId, int diff) {
        if (diff > 0) {
            // 盘盈：加行锁后原子性增加最新批次库存
            DrugBatch latestBatch = drugBatchMapper.selectLatestForUpdate(drugId);
            if (latestBatch != null) {
                drugBatchMapper.incrementStock(latestBatch.getId(), diff);
            } else {
                Drug drug = drugMapper.selectById(drugId);
                DrugBatch newBatch = new DrugBatch();
                newBatch.setDrugId(drugId);
                newBatch.setPrice(drug != null ? drug.getPrice() : BigDecimal.ZERO);
                newBatch.setStockQuantity(diff);
                newBatch.setInitialQuantity(diff);
                newBatch.setCreatedAt(LocalDateTime.now());
                newBatch.setBatchNo("INV_CHECK_AUTO");
                drugBatchMapper.insert(newBatch);
            }
        } else {
            // 盘亏：FIFO 扣减（加行锁防并发）
            int toDeduct = Math.abs(diff);
            List<DrugBatch> batches = drugBatchMapper.selectBatchesForUpdate(drugId);

            for (DrugBatch batch : batches) {
                if (toDeduct <= 0) break;
                int deductAmount = Math.min(batch.getStockQuantity(), toDeduct);
                drugBatchMapper.incrementStock(batch.getId(), -deductAmount);
                toDeduct -= deductAmount;
            }
        }
    }

    @Override
    public void reopenTask(Long taskId) {
        InventoryCheckTask task = taskMapper.selectById(taskId);
        if (task == null) throw new BusinessException("任务不存在");
        
        task.setStatus("PENDING");
        task.setCompletedAt(null);
        taskMapper.updateById(task);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteTask(Long taskId) {
        // 1. 删除明细
        QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
        detailWrapper.eq("task_id", taskId);
        detailMapper.delete(detailWrapper);
        
        // 2. 删除主任务
        taskMapper.deleteById(taskId);
    }

    @Override
    public List<InventoryCheckTask> getPendingTasks() {
        QueryWrapper<InventoryCheckTask> wrapper = new QueryWrapper<>();
        wrapper.eq("status", "PENDING");
        return taskMapper.selectList(wrapper);
    }
}
