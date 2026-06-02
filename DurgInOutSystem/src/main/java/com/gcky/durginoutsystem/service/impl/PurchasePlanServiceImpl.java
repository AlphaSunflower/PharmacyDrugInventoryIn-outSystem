package com.gcky.durginoutsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.entity.PurchasePlan;
import com.gcky.durginoutsystem.entity.PurchasePlanDetail;
import com.gcky.durginoutsystem.exception.BusinessException;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.PurchasePlanDetailMapper;
import com.gcky.durginoutsystem.mapper.PurchasePlanMapper;
import com.gcky.durginoutsystem.service.PurchasePlanService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class PurchasePlanServiceImpl implements PurchasePlanService {

    @Autowired
    private PurchasePlanMapper planMapper;
    @Autowired
    private PurchasePlanDetailMapper detailMapper;
    @Autowired
    private DrugMapper drugMapper;
    @Autowired
    private DrugBatchMapper drugBatchMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long generatePlan(String month) {
        // 1. 检查该月计划是否已存在
        QueryWrapper<PurchasePlan> wrapper = new QueryWrapper<>();
        wrapper.eq("month", month);
        PurchasePlan exist = planMapper.selectOne(wrapper);
        if (exist != null) {
            return exist.getId();
        }

        // 2. 创建新计划
        PurchasePlan plan = new PurchasePlan();
        plan.setMonth(month);
        plan.setStatus("PENDING");
        plan.setCreatedAt(LocalDateTime.now());
        planMapper.insert(plan);

        // 3. 生成明细（拉取所有非删除药品的快照数据）
        List<Drug> drugs = drugMapper.selectList(new QueryWrapper<Drug>().eq("is_deleted", 0));
        for (Drug drug : drugs) {
            PurchasePlanDetail detail = new PurchasePlanDetail();
            detail.setPlanId(plan.getId());
            detail.setDrugId(drug.getId());
            detail.setSpec(drug.getSpec());
            detail.setUnit(drug.getUnit());

            // 取最新批次的进货价和生产厂家
            DrugBatch latestBatch = drugBatchMapper.selectLatestByDrugId(drug.getId());
            if (latestBatch != null) {
                detail.setPurchasePrice(latestBatch.getPrice());
                detail.setManufacturer(latestBatch.getManufacturer());
            }

            detail.setPlannedQuantity(null);
            detail.setCreatedAt(LocalDateTime.now());
            detailMapper.insert(detail);
        }

        return plan.getId();
    }

    @Override
    public List<Map<String, Object>> getPlanDetails(Long planId) {
        QueryWrapper<PurchasePlanDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("plan_id", planId);
        List<PurchasePlanDetail> details = detailMapper.selectList(wrapper);

        // 批量加载药品名称（消除 N+1）
        List<Long> drugIds = details.stream().map(PurchasePlanDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        return details.stream().map(d -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", d.getId());
            map.put("planId", d.getPlanId());
            map.put("drugId", d.getDrugId());
            Drug drug = drugMap.get(d.getDrugId());
            map.put("drugName", drug != null ? drug.getName() : "Unknown");
            map.put("spec", d.getSpec());
            map.put("unit", d.getUnit());
            map.put("purchasePrice", d.getPurchasePrice());
            map.put("manufacturer", d.getManufacturer());
            map.put("plannedQuantity", d.getPlannedQuantity());
            return map;
        }).collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateDetail(Long detailId, Integer plannedQuantity, String manufacturer) {
        PurchasePlanDetail detail = detailMapper.selectById(detailId);
        if (detail == null) return;

        if (plannedQuantity != null) {
            detail.setPlannedQuantity(plannedQuantity);
        }
        if (manufacturer != null) {
            detail.setManufacturer(manufacturer);
        }
        detailMapper.updateById(detail);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void completePlan(Long planId) {
        // 校验所有计划数量已填写
        QueryWrapper<PurchasePlanDetail> wrapper = new QueryWrapper<>();
        wrapper.eq("plan_id", planId);
        List<PurchasePlanDetail> details = detailMapper.selectList(wrapper);

        // 批量加载药品名称
        List<Long> drugIds = details.stream().map(PurchasePlanDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        for (PurchasePlanDetail detail : details) {
            if (detail.getPlannedQuantity() == null || detail.getPlannedQuantity() <= 0) {
                Drug drug = drugMap.get(detail.getDrugId());
                String drugName = drug != null ? drug.getName() : "未知药品";
                throw new BusinessException("药品 [" + drugName + "] 的计划数量未填写，请填写后再完成");
            }
        }

        // 更新计划状态
        PurchasePlan plan = new PurchasePlan();
        plan.setId(planId);
        plan.setStatus("COMPLETED");
        planMapper.updateById(plan);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void reopenPlan(Long planId) {
        PurchasePlan plan = planMapper.selectById(planId);
        if (plan == null) throw new BusinessException("采购计划不存在");

        plan.setStatus("PENDING");
        planMapper.updateById(plan);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deletePlan(Long planId) {
        // 1. 删除明细
        QueryWrapper<PurchasePlanDetail> detailWrapper = new QueryWrapper<>();
        detailWrapper.eq("plan_id", planId);
        detailMapper.delete(detailWrapper);

        // 2. 删除主计划
        planMapper.deleteById(planId);
    }
}
