package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.gcky.durginoutsystem.entity.OperationLog;
import java.util.Map;

public interface OperationLogService extends IService<OperationLog> {
    Page<Map<String, Object>> getLogs(Integer page, Integer size, String keyword);
    void deleteAllLogs();
    void deleteOldLogs(int months);
}
