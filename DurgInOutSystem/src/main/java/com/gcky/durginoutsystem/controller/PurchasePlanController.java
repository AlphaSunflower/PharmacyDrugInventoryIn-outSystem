package com.gcky.durginoutsystem.controller;

import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.entity.PurchasePlan;
import com.gcky.durginoutsystem.mapper.PurchasePlanMapper;
import com.gcky.durginoutsystem.service.PurchasePlanService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole({"DOCTOR", "PHARMACIST"})
@RestController
@RequestMapping("/api/v1/purchase-plans")
public class PurchasePlanController {

    @Autowired
    private PurchasePlanService purchasePlanService;
    @Autowired
    private PurchasePlanMapper planMapper;
    @Autowired
    private com.gcky.durginoutsystem.mapper.DrugBatchMapper drugBatchMapper;

    // 生成或获取采购计划
    @PostMapping("/generate")
    public Result<Map<String, Object>> generatePlan(@RequestParam String month) {
        Long planId = purchasePlanService.generatePlan(month);
        PurchasePlan plan = planMapper.selectById(planId);
        Map<String, Object> result = new HashMap<>();
        result.put("planId", planId);
        result.put("status", plan != null ? plan.getStatus() : "PENDING");
        return Result.success(result);
    }

    // 获取计划明细
    @GetMapping("/{planId}/details")
    public Result<List<Map<String, Object>>> getPlanDetails(@PathVariable Long planId) {
        return Result.success(purchasePlanService.getPlanDetails(planId));
    }

    // 更新明细（计划数量 / 生产厂家）
    @PutMapping("/details/{detailId}")
    public Result<String> updateDetail(@PathVariable Long detailId, @RequestBody Map<String, Object> body) {
        Integer plannedQuantity = null;
        if (body.get("plannedQuantity") != null) {
            plannedQuantity = ((Number) body.get("plannedQuantity")).intValue();
        }
        String manufacturer = (String) body.get("manufacturer");
        purchasePlanService.updateDetail(detailId, plannedQuantity, manufacturer);
        return Result.success("更新成功");
    }

    // 完成采购计划
    @PostMapping("/{planId}/complete")
    public Result<String> completePlan(@PathVariable Long planId) {
        purchasePlanService.completePlan(planId);
        return Result.success("采购计划已完成");
    }

    // 重新修改（解锁编辑）
    @PostMapping("/{planId}/reopen")
    public Result<String> reopenPlan(@PathVariable Long planId) {
        purchasePlanService.reopenPlan(planId);
        return Result.success("采购计划已重新开启，可进行修改");
    }

    // 删除采购计划
    @DeleteMapping("/{planId}")
    public Result<String> deletePlan(@PathVariable Long planId) {
        purchasePlanService.deletePlan(planId);
        return Result.success("采购计划已删除");
    }

    // 获取某药品的历史生产厂家列表（新→旧，去重）
    @GetMapping("/drug/{drugId}/manufacturers")
    public Result<List<String>> getDrugManufacturers(@PathVariable Long drugId) {
        List<DrugBatch> batches = drugBatchMapper.selectAllByDrugIdOrderByCreatedAtDesc(drugId);
        List<String> manufacturers = batches.stream()
                .map(DrugBatch::getManufacturer)
                .filter(m -> m != null && !m.trim().isEmpty())
                .distinct()
                .collect(java.util.stream.Collectors.toList());
        return Result.success(manufacturers);
    }
}
