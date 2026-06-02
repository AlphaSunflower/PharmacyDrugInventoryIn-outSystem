package com.gcky.durginoutsystem.controller;

import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.InventoryCheckTask;
import com.gcky.durginoutsystem.service.InventoryService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole("PHARMACIST")
@RestController
@RequestMapping("/api/v1/inventory-checks")
public class InventoryController {

    private final InventoryService inventoryService;

    public InventoryController(InventoryService inventoryService) {
        this.inventoryService = inventoryService;
    }

    // 生成或获取盘点任务
    @PostMapping("/generate")
    public Result<Long> generateTask(@RequestParam String month) {
        return Result.success(inventoryService.generateTask(month));
    }

    // 获取任务明细
    @GetMapping("/{taskId}/details")
    public Result<List<Map<String, Object>>> getTaskDetails(@PathVariable Long taskId) {
        return Result.success(inventoryService.getTaskDetails(taskId));
    }

    // 录入盘点数据
    @PutMapping("/details/{detailId}")
    public Result<String> updateDetail(@PathVariable Long detailId, @RequestBody Map<String, Object> body) {
        Integer actualStock = (Integer) body.get("actualStock");
        String remark = (String) body.get("remark");
        inventoryService.updateDetail(detailId, actualStock, remark);
        return Result.success("录入成功");
    }

    // 完成任务
    @PostMapping("/{taskId}/complete")
    public Result<String> completeTask(@PathVariable Long taskId) {
        inventoryService.completeTask(taskId);
        return Result.success("盘点任务已完成");
    }
    
    // 修改盘点任务状态为PENDING（允许重新修改）
    @PostMapping("/{taskId}/reopen")
    public Result<String> reopenTask(@PathVariable Long taskId) {
        inventoryService.reopenTask(taskId);
        return Result.success("盘点任务已重新开启，可进行修改");
    }

    // 删除盘点任务
    @DeleteMapping("/{taskId}")
    public Result<String> deleteTask(@PathVariable Long taskId) {
        inventoryService.deleteTask(taskId);
        return Result.success("盘点任务已删除");
    }

    // 获取未完成任务 (用于逾期提醒)
    @GetMapping("/pending")
    public Result<List<InventoryCheckTask>> getPendingTasks() {
        return Result.success(inventoryService.getPendingTasks());
    }
}
