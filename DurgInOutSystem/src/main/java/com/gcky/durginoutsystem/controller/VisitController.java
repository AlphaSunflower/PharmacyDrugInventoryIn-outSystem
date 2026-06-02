package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.dto.VisitSubmitDTO;
import com.gcky.durginoutsystem.service.VisitService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/v1/visits")
public class VisitController {

    private final VisitService visitService;

    public VisitController(VisitService visitService) {
        this.visitService = visitService;
    }

    @Log("提交就诊记录")
    @RequireRole("DOCTOR")
    @PostMapping
    public Result<String> submitVisit(HttpServletRequest request,
                                      @Valid @RequestBody VisitSubmitDTO visitDTO) {
        Long userId = (Long) request.getAttribute("userId");
        visitService.submitVisit(userId, visitDTO);
        return Result.success("提交成功");
    }

    @GetMapping
    public Result<Page<Map<String, Object>>> getVisits(HttpServletRequest request,
                                                       @RequestParam(defaultValue = "1") Integer page,
                                                       @RequestParam(defaultValue = "10") Integer size,
                                                       @RequestParam(required = false) String status,
                                                       @RequestParam(required = false) String keyword,
                                                       @RequestParam(required = false) String startDate,
                                                       @RequestParam(required = false) String endDate,
                                                       @RequestParam(required = false) Long diagnosisId,
                                                       @RequestParam(required = false) String department,
                                                       @RequestParam(required = false) String drugName) {
        String role = (String) request.getAttribute("role");
        Long userId = (Long) request.getAttribute("userId");

        Long queryDoctorId = null;
        if ("DOCTOR".equals(role)) {
            queryDoctorId = userId;
        }

        return Result.success(visitService.getVisits(page, size, status, queryDoctorId, keyword, startDate, endDate, diagnosisId, department, drugName));
    }

    @Log("药师发药")
    @RequireRole("PHARMACIST")
    @PostMapping("/{id}/dispense")
    public Result<String> dispense(@PathVariable Long id) {
        visitService.dispense(id);
        return Result.success("发药成功");
    }

    @Log("药师退回处方")
    @RequireRole("PHARMACIST")
    @PostMapping("/{id}/return")
    public Result<String> returnVisit(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String reason = body.get("reason");
        visitService.returnVisit(id, reason);
        return Result.success("已退回");
    }

    @Log("医师修改重提就诊记录")
    @RequireRole("DOCTOR")
    @PutMapping("/{id}")
    public Result<String> updateVisit(@PathVariable Long id, @Valid @RequestBody VisitSubmitDTO visitDTO) {
        visitService.updateVisit(id, visitDTO);
        return Result.success("修改并重新提交成功");
    }

    @Log("取消就诊记录")
    @RequireRole("DOCTOR")
    @PostMapping("/{id}/cancel")
    public Result<String> cancelVisit(@PathVariable Long id) {
        visitService.cancelVisit(id);
        return Result.success("就诊记录已取消");
    }

    /** 通知计数：待发药数 / 已退回数 / 新完成数，供前端轮询红点和弹窗 */
    @GetMapping("/notification-counts")
    public Result<Map<String, Object>> notificationCounts(HttpServletRequest request) {
        String role = (String) request.getAttribute("role");
        Long userId = (Long) request.getAttribute("userId");
        Map<String, Object> counts = new HashMap<>();
        counts.put("pendingCount", visitService.countByStatus("SUBMITTED", null));
        if (!"PHARMACIST".equals(role)) {
            counts.put("returnedCount", visitService.countByStatus("RETURNED", userId));
        }
        return Result.success(counts);
    }
}
