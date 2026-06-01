package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.service.OperationLogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole("ADMIN")
@RestController
@RequestMapping("/api/v1/operation-logs")
public class OperationLogController {

    @Autowired
    private OperationLogService operationLogService;

    // 获取日志列表
    @GetMapping
    public Result<Page<Map<String, Object>>> getLogs(@RequestParam(defaultValue = "1") Integer page,
                                                     @RequestParam(defaultValue = "10") Integer size,
                                                     @RequestParam(required = false) String keyword) {
        return Result.success(operationLogService.getLogs(page, size, keyword));
    }

    // 删除所有日志
    @DeleteMapping
    public Result<String> deleteAllLogs() {
        operationLogService.deleteAllLogs();
        return Result.success("所有日志已清空");
    }
}
