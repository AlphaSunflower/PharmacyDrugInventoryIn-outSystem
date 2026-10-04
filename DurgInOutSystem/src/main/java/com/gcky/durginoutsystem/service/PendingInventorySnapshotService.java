package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.InventoryCheckDetail;
import com.gcky.durginoutsystem.entity.InventoryCheckTask;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckDetailMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckTaskMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class PendingInventorySnapshotService {

    public static final String STOCK_CHANGED_LOG =
            "该药品系统库存发生改变，请重新核实库存数量";

    @Autowired
    private InventoryCheckTaskMapper taskMapper;
    @Autowired
    private InventoryCheckDetailMapper detailMapper;
    @Autowired
    private DrugMapper drugMapper;

    /** 按业务日期月份同步待完成盘点任务中该药品的系统库存。 */
    public void syncDrugStock(Long drugId, LocalDate businessDate) {
        if (drugId == null) {
            return;
        }

        String month = (businessDate != null ? businessDate : LocalDate.now()).toString().substring(0, 7);
        InventoryCheckTask task = taskMapper.selectOne(new QueryWrapper<InventoryCheckTask>()
                .eq("month", month)
                .eq("status", "PENDING"));
        if (task == null) {
            return;
        }

        InventoryCheckDetail detail = detailMapper.selectOne(new QueryWrapper<InventoryCheckDetail>()
                .eq("task_id", task.getId())
                .eq("drug_id", drugId));
        if (detail == null) {
            return;
        }

        Drug drug = drugMapper.selectById(drugId);
        if (drug != null) {
            updateDetailIfChanged(detail, drug.getStockQuantity());
        }
    }

    /** 全量对账单个待完成盘点任务，补上未经过库存服务的变更。 */
    public void syncTaskSnapshot(Long taskId) {
        InventoryCheckTask task = taskMapper.selectById(taskId);
        if (task == null || !"PENDING".equals(task.getStatus())) {
            return;
        }

        List<InventoryCheckDetail> details = detailMapper.selectList(
                new QueryWrapper<InventoryCheckDetail>().eq("task_id", taskId));
        if (details.isEmpty()) {
            return;
        }

        List<Long> drugIds = details.stream()
                .map(InventoryCheckDetail::getDrugId)
                .distinct()
                .collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream()
                        .collect(Collectors.toMap(Drug::getId, drug -> drug));

        for (InventoryCheckDetail detail : details) {
            Drug drug = drugMap.get(detail.getDrugId());
            if (drug != null) {
                updateDetailIfChanged(detail, drug.getStockQuantity());
            }
        }
    }

    private void updateDetailIfChanged(InventoryCheckDetail detail, Integer currentStock) {
        if (Objects.equals(detail.getSystemStock(), currentStock)) {
            return;
        }

        detail.setSystemStock(currentStock);
        if (detail.getActualStock() != null) {
            detail.setLogContent(STOCK_CHANGED_LOG);
        }
        detailMapper.updateById(detail);
    }
}
