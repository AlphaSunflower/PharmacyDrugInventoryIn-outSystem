package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.dto.VisitSubmitDTO;
import com.gcky.durginoutsystem.service.VisitService;
import com.gcky.durginoutsystem.utils.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

import com.gcky.durginoutsystem.annotation.Log;

@Slf4j
@RestController
@RequestMapping("/api/v1/visits")
@CrossOrigin
public class VisitController {

    @Autowired
    private VisitService visitService;
    @Autowired
    private JwtUtil jwtUtil;

    // 提交就诊记录
    @Log("提交就诊记录")
    @PostMapping
    public Result<String> submitVisit(@RequestHeader("Authorization") String token,
                                      @RequestBody VisitSubmitDTO visitDTO) {
        Long userId = getUserIdFromToken(token);
        visitService.submitVisit(userId, visitDTO);
        return Result.success("提交成功");
    }

    // 获取列表 (医师看自己的，药师看所有的/待办的)
    @GetMapping
    public Result<Page<Map<String, Object>>> getVisits(@RequestHeader("Authorization") String token,
                                                       @RequestParam(defaultValue = "1") Integer page,
                                                       @RequestParam(defaultValue = "10") Integer size,
                                                       @RequestParam(required = false) String status,
                                                       @RequestParam(required = false) String keyword,
                                                       @RequestParam(required = false) String startDate,
                                                       @RequestParam(required = false) String endDate,
                                                       @RequestParam(required = false) Long diagnosisId,
                                                       @RequestParam(required = false) String department,
                                                       @RequestParam(required = false) String drugName) {
        String role = getRoleFromToken(token);
        Long userId = getUserIdFromToken(token);
        log.info("登录的token" + token);
        Long queryDoctorId = null;
        if ("DOCTOR".equals(role)) {
            queryDoctorId = userId;
        }

        return Result.success(visitService.getVisits(page, size, status, queryDoctorId, keyword, startDate, endDate, diagnosisId, department, drugName));
    }

    // 药师发药
    @Log("药师发药")
    @PostMapping("/{id}/dispense")
    public Result<String> dispense(@PathVariable Long id) {
        visitService.dispense(id);
        return Result.success("发药成功");
    }

    // 药师退回
    @Log("药师退回处方")
    @PostMapping("/{id}/return")
    public Result<String> returnVisit(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String reason = body.get("reason");
        visitService.returnVisit(id, reason);
        return Result.success("已退回");
    }

    // 医师修改重提
    @Log("医师修改重提就诊记录")
    @PutMapping("/{id}")
    public Result<String> updateVisit(@PathVariable Long id, @RequestBody VisitSubmitDTO visitDTO) {
        visitService.updateVisit(id, visitDTO);
        return Result.success("修改并重新提交成功");
    }

    // 取消就诊记录
    @Log("取消就诊记录")
    @PostMapping("/{id}/cancel")
    public Result<String> cancelVisit(@PathVariable Long id) {
        visitService.cancelVisit(id);
        return Result.success("就诊记录已取消");
    }


    private Long getUserIdFromToken(String token) {
        if (token.startsWith("Bearer ")) token = token.substring(7);
        return jwtUtil.extractClaims(token).get("userId", Long.class);
    }

    private String getRoleFromToken(String token) {
        if (token.startsWith("Bearer ")) token = token.substring(7);
        return jwtUtil.extractClaims(token).get("role", String.class);
    }
}
