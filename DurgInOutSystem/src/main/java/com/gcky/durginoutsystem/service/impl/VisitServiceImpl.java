package com.gcky.durginoutsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.entity.DiagnosisType;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.PatientVisit;
import com.gcky.durginoutsystem.entity.VisitDrug;
import com.gcky.durginoutsystem.entity.dto.VisitSubmitDTO;
import com.gcky.durginoutsystem.mapper.DiagnosisTypeMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.PatientVisitMapper;
import com.gcky.durginoutsystem.mapper.VisitDrugMapper;
import com.gcky.durginoutsystem.service.VisitService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Slf4j
public class VisitServiceImpl implements VisitService {

    @Autowired
    private PatientVisitMapper visitMapper;
    @Autowired
    private VisitDrugMapper visitDrugMapper;
    @Autowired
    private DrugMapper drugMapper;
    @Autowired
    private DiagnosisTypeMapper diagnosisTypeMapper;
    @Autowired
    private com.gcky.durginoutsystem.mapper.DrugBatchMapper drugBatchMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void submitVisit(Long doctorId, VisitSubmitDTO visitDTO) {
        // 1. 保存就诊记录
        PatientVisit visit = new PatientVisit();
        BeanUtils.copyProperties(visitDTO, visit);
        visit.setDoctorId(doctorId);
        visit.setStatus("SUBMITTED");
        visit.setCreatedAt(LocalDateTime.now());
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.insert(visit);

        // 2. 保存处方药品
        saveVisitDrugs(visit.getId(), visitDTO.getDrugs());
    }

    private void saveVisitDrugs(Long visitId, List<VisitSubmitDTO.VisitDrugDTO> drugs) {
        for (VisitSubmitDTO.VisitDrugDTO drugDTO : drugs) {
            Drug drug = drugMapper.selectById(drugDTO.getDrugId());
            if (drug == null) {
                throw new RuntimeException("药品不存在 ID: " + drugDTO.getDrugId());
            }

            int remaining = drugDTO.getQuantity();
            if (remaining <= 0) continue;

            // 获取有效批次 (FIFO)
            QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> query = new QueryWrapper<>();
            query.eq("drug_id", drugDTO.getDrugId())
                 .gt("stock_quantity", 0)
                 .orderByAsc("created_at");
            List<com.gcky.durginoutsystem.entity.DrugBatch> batches = drugBatchMapper.selectList(query);

            // 按照批次拆分记录
            for (com.gcky.durginoutsystem.entity.DrugBatch batch : batches) {
                if (remaining <= 0) break;
                
                int take = Math.min(remaining, batch.getStockQuantity());
                
                VisitDrug visitDrug = new VisitDrug();
                visitDrug.setVisitId(visitId);
                visitDrug.setDrugId(drugDTO.getDrugId());
                visitDrug.setQuantity(take);
                visitDrug.setPrice(batch.getPrice()); // 使用该批次的单价
                visitDrug.setAmount(batch.getPrice().multiply(new BigDecimal(take)));
                visitDrugMapper.insert(visitDrug);
                
                remaining -= take;
            }

            // 如果库存不足，剩余部分按参考价记录 (或者按最新批次价)
            if (remaining > 0) {
                VisitDrug visitDrug = new VisitDrug();
                visitDrug.setVisitId(visitId);
                visitDrug.setDrugId(drugDTO.getDrugId());
                visitDrug.setQuantity(remaining);
                visitDrug.setPrice(drug.getPrice()); 
                visitDrug.setAmount(drug.getPrice().multiply(new BigDecimal(remaining)));
                visitDrugMapper.insert(visitDrug);
            }
        }
    }

    @Override
    public Page<Map<String, Object>> getVisits(Integer page, Integer size, String status, Long doctorId, String keyword, String startDate, String endDate, Long diagnosisId, String department, String drugName) {
        // 这里需要自定义 SQL 连接查询 (为了展示医生姓名、诊断名称等)，简化起见，这里演示逻辑
        // 实际项目建议在 Mapper.xml 中编写多表联查
        // 此处暂时返回基础分页，具体字段组装可根据前端需求优化
        Page<PatientVisit> p = new Page<>(page, size);
        QueryWrapper<PatientVisit> wrapper = new QueryWrapper<>();
        
        // 状态筛选
        if (status != null && !status.isEmpty()) {
            wrapper.eq("status", status);
        }
        // 医生权限筛选
        if (doctorId != null) {
            wrapper.eq("doctor_id", doctorId);
        }
        // 模糊查询 (姓名)
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like("patient_name", keyword);
        }
        // 日期范围查询
        if (startDate != null && !startDate.isEmpty()) {
            wrapper.ge("visit_date", startDate);
        }
        if (endDate != null && !endDate.isEmpty()) {
            wrapper.le("visit_date", endDate);
        }
        // 诊断类型筛选
        if (diagnosisId != null) {
            wrapper.eq("diagnosis_id", diagnosisId);
        }
        // 部门筛选
        if (department != null && !department.isEmpty()) {
            wrapper.eq("department", department);
        }
        
        // 药品名称筛选 (新增)
        if (drugName != null && !drugName.trim().isEmpty()) {
            QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
            drugQuery.like("name", drugName.trim());
            List<Drug> drugs = drugMapper.selectList(drugQuery);
            
            if (drugs.isEmpty()) {
                return new Page<>(page, size);
            }
            
            List<Long> drugIds = drugs.stream().map(Drug::getId).collect(Collectors.toList());
            
            QueryWrapper<VisitDrug> vdQuery = new QueryWrapper<>();
            vdQuery.in("drug_id", drugIds);
            vdQuery.select("DISTINCT visit_id");
            List<Object> visitIds = visitDrugMapper.selectObjs(vdQuery);
            
            if (visitIds.isEmpty()) {
                 return new Page<>(page, size);
            }
            
            wrapper.in("id", visitIds);
        }

        wrapper.orderByDesc("created_at");
        
        Page<PatientVisit> resultPage = visitMapper.selectPage(p, wrapper);
        
        // 转换为 Map 并填充关联信息 (简单实现)
        Page<Map<String, Object>> mapPage = new Page<>(page, size, resultPage.getTotal());
        List<Map<String, Object>> records = resultPage.getRecords().stream().map(visit -> {
            Map<String, Object> map = new HashMap<>();
            // 使用 BeanUtils.copyProperties 将属性复制到 Map 是不可行的，BeanUtils 只能用于 Bean 之间
            // 正确做法是手动 put 或者将 Bean 转为 Map
            // 这里我们使用手动 put 关键字段，或者使用 Jackson/Fastjson 转 Map
            // 简单起见，我们手动 put 所有字段
            map.put("id", visit.getId());
            map.put("patientName", visit.getPatientName());
            map.put("visitDate", visit.getVisitDate());
            map.put("status", visit.getStatus());
            map.put("diagnosisId", visit.getDiagnosisId());
            if (visit.getDiagnosisId() != null) {
                DiagnosisType dt = diagnosisTypeMapper.selectById(visit.getDiagnosisId());
                map.put("diagnosisName", dt != null ? dt.getName() : "");
            } else if (visit.getCustomDiagnosis() != null) {
                map.put("diagnosisName", visit.getCustomDiagnosis() + " (自定义)");
            } else {
                map.put("diagnosisName", "");
            }

            map.put("returnReason", visit.getReturnReason());
            map.put("doctorId", visit.getDoctorId());

            map.put("gender", visit.getGender());
            map.put("age", visit.getAge());
            map.put("department", visit.getDepartment());
            
            // 填充药品列表
            QueryWrapper<VisitDrug> drugWrapper = new QueryWrapper<>();
            drugWrapper.eq("visit_id", visit.getId());
            List<VisitDrug> drugs = visitDrugMapper.selectList(drugWrapper);
            
            List<Map<String, Object>> drugDetails = drugs.stream().map(d -> {
                Map<String, Object> dm = new HashMap<>();
                // BeanUtils.copyProperties(d, dm); // BeanUtils copy properties to Map is not working as expected
                dm.put("id", d.getId());
                dm.put("visitId", d.getVisitId());
                dm.put("drugId", d.getDrugId());
                dm.put("quantity", d.getQuantity());
                dm.put("amount", d.getAmount());
                
                Drug drug = drugMapper.selectById(d.getDrugId());
                dm.put("drugName", drug != null ? drug.getName() : "Unknown");
                dm.put("drugSpec", drug != null ? drug.getSpec() : "");
                
                // Add fields expected by frontend
                dm.put("spec", drug != null ? drug.getSpec() : "");
                
                // 优先使用记录的实际单价，否则使用参考价
                if (d.getPrice() != null) {
                    dm.put("price", d.getPrice());
                } else {
                    dm.put("price", drug != null ? drug.getPrice() : BigDecimal.ZERO);
                }
                // batchId 已废弃
                dm.put("batchId", null);
                
                return dm;
            }).collect(Collectors.toList());

            map.put("drugs", drugDetails);
            return map;
        }).collect(Collectors.toList());
        
        mapPage.setRecords(records);
        return mapPage;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispense(Long visitId) {
        PatientVisit visit = visitMapper.selectById(visitId);
        if (visit == null || !"SUBMITTED".equals(visit.getStatus())) {
            throw new RuntimeException("工单状态不正确或不存在");
        }

        // 1. 获取处方药品
        QueryWrapper<VisitDrug> drugWrapper = new QueryWrapper<>();
        drugWrapper.eq("visit_id", visitId);
        List<VisitDrug> visitDrugs = visitDrugMapper.selectList(drugWrapper);

        for (VisitDrug vd : visitDrugs) {
            Drug drug = drugMapper.selectById(vd.getDrugId());
            if (drug == null) throw new RuntimeException("药品不存在");

            // FIFO 动态扣减逻辑
            int needed = vd.getQuantity();
            
            // 查询所有有效批次 (FIFO)
            QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> batchQuery = new QueryWrapper<>();
            batchQuery.eq("drug_id", drug.getId())
                      .gt("stock_quantity", 0)
                      .orderByAsc("created_at");
            List<com.gcky.durginoutsystem.entity.DrugBatch> batches = drugBatchMapper.selectList(batchQuery);
            
            for (com.gcky.durginoutsystem.entity.DrugBatch batch : batches) {
                if (needed <= 0) break;
                
                int take = Math.min(needed, batch.getStockQuantity());
                
                batch.setStockQuantity(batch.getStockQuantity() - take);
                drugBatchMapper.updateById(batch);
                
                needed -= take;
            }
            
            if (needed > 0) {
                 // 批次扣完了还不够？ (说明总库存 < 账面库存，或有其他并发问题)
                 throw new RuntimeException("药品库存严重不足: " + drug.getName() + " (缺 " + needed + ")");
            }

            // 同步更新 Drug 总库存 (基于所有批次的总和)
            updateDrugTotalStock(drug.getId());
        }

        // 2. 更新状态
        visit.setStatus("COMPLETED");
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.updateById(visit);
    }

    /**
     * 重新计算并更新药品总库存 (基于所有批次库存之和)
     */
    private void updateDrugTotalStock(Long drugId) {
        QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> query = new QueryWrapper<>();
        query.eq("drug_id", drugId);
        // 注意：这里需要统计所有批次，包括库存为0的(如果没删的话)，或者只统计 > 0 的
        // 建议只统计 > 0 的，假设 <= 0 的批次库存确实为0
        query.select("IFNULL(SUM(stock_quantity), 0) as total");
        
        Map<String, Object> result = drugBatchMapper.selectMaps(query).stream().findFirst().orElse(null);
        int totalStock = 0;
        if (result != null && result.get("total") != null) {
            totalStock = ((BigDecimal) result.get("total")).intValue();
        }
        
        Drug drug = new Drug();
        drug.setId(drugId);
        drug.setStockQuantity(totalStock);
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.updateById(drug);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void returnVisit(Long visitId, String reason) {
        PatientVisit visit = visitMapper.selectById(visitId);
        if (visit == null) {
            throw new RuntimeException("记录不存在");
        }
        
        // 如果是已完成的订单退回（退药），需要恢复库存
        if ("COMPLETED".equals(visit.getStatus())) {
            QueryWrapper<VisitDrug> wrapper = new QueryWrapper<>();
            wrapper.eq("visit_id", visitId);
            List<VisitDrug> visitDrugs = visitDrugMapper.selectList(wrapper);
            
            for (VisitDrug vd : visitDrugs) {
                // 恢复库存 (直接退回最新批次)
                restoreToLatestBatch(vd.getDrugId(), vd.getQuantity(), vd.getPrice());

                // 恢复总库存 (重新计算)
                updateDrugTotalStock(vd.getDrugId());
            }
        }
        
        visit.setStatus("RETURNED");
        visit.setReturnReason(reason);
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.updateById(visit);
    }

    private void restoreToLatestBatch(Long drugId, Integer quantity, BigDecimal price) {
        QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> query = new QueryWrapper<>();
        query.eq("drug_id", drugId)
             .orderByDesc("created_at")
             .last("LIMIT 1");
        com.gcky.durginoutsystem.entity.DrugBatch latest = drugBatchMapper.selectOne(query);
        
        if (latest != null) {
            latest.setStockQuantity(latest.getStockQuantity() + quantity);
            drugBatchMapper.updateById(latest);
        } else {
            // 创建恢复批次
            com.gcky.durginoutsystem.entity.DrugBatch batch = new com.gcky.durginoutsystem.entity.DrugBatch();
            batch.setDrugId(drugId);
            batch.setBatchNo("RETURN_RESTORE");
            batch.setPrice(price != null ? price : BigDecimal.ZERO);
            batch.setStockQuantity(quantity);
            batch.setInitialQuantity(quantity);
            batch.setCreatedAt(LocalDateTime.now());
            drugBatchMapper.insert(batch);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateVisit(Long visitId, VisitSubmitDTO visitDTO) {
        PatientVisit visit = visitMapper.selectById(visitId);
        if (visit == null || !"RETURNED".equals(visit.getStatus())) {
            throw new RuntimeException("仅已退回的记录可修改");
        }
        
        // 更新基础信息
        BeanUtils.copyProperties(visitDTO, visit, "id", "doctorId", "createdAt");
        visit.setStatus("SUBMITTED"); // 重新提交
        visit.setReturnReason(null);  // 清空退回原因
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.updateById(visit);

        // 删除旧药品明细
        QueryWrapper<VisitDrug> wrapper = new QueryWrapper<>();
        wrapper.eq("visit_id", visitId);
        visitDrugMapper.delete(wrapper);

        // 重新保存药品明细
        saveVisitDrugs(visitId, visitDTO.getDrugs());
    }

    @Override
    public void cancelVisit(Long visitId) {
        PatientVisit visit = visitMapper.selectById(visitId);
        if (visit == null) {
            throw new RuntimeException("记录不存在");
        }
        
        // 只能取消 待发药(SUBMITTED) 或 已退回(RETURNED) 的记录
        // DRAFT 理论上也可以，但前端可能没入口。COMPLETED 已完成发药不能直接取消(需要退药流程)，CANCELED 已取消
        if (!"SUBMITTED".equals(visit.getStatus()) && !"RETURNED".equals(visit.getStatus())) {
            throw new RuntimeException("当前状态不可取消");
        }
        
        visit.setStatus("CANCELED");
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.updateById(visit);
    }
}
