package com.gcky.durginoutsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.gcky.durginoutsystem.entity.OperationLog;
import com.gcky.durginoutsystem.entity.User;
import com.gcky.durginoutsystem.mapper.OperationLogMapper;
import com.gcky.durginoutsystem.mapper.UserMapper;
import com.gcky.durginoutsystem.service.OperationLogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class OperationLogServiceImpl extends ServiceImpl<OperationLogMapper, OperationLog> implements OperationLogService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public Page<Map<String, Object>> getLogs(Integer page, Integer size, String keyword) {
        Page<OperationLog> p = new Page<>(page, size);
        QueryWrapper<OperationLog> wrapper = new QueryWrapper<>();
        
        if (keyword != null && !keyword.isEmpty()) {
             wrapper.like("action", keyword);
        }
        
        wrapper.orderByDesc("created_at");
        
        Page<OperationLog> resultPage = this.page(p, wrapper);

        // 批量加载用户信息（消除 N+1）
        List<Long> userIds = resultPage.getRecords().stream()
                .map(OperationLog::getUserId).filter(id -> id != null).distinct().collect(Collectors.toList());
        Map<Long, User> userMap = userIds.isEmpty() ? Collections.emptyMap() :
                userMapper.selectBatchIds(userIds).stream().collect(Collectors.toMap(User::getId, u -> u));

        Page<Map<String, Object>> mapPage = new Page<>(page, size, resultPage.getTotal());

        List<Map<String, Object>> records = resultPage.getRecords().stream().map(log -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", log.getId());
            map.put("action", log.getAction());
            map.put("createdAt", log.getCreatedAt());
            map.put("userId", log.getUserId());
            map.put("operateData", log.getOperateData());

            if (log.getRole() != null) {
                map.put("role", log.getRole());
            }

            if (log.getUserId() != null) {
                User user = userMap.get(log.getUserId());
                map.put("username", user != null ? user.getUsername() : "Unknown");
                if (!map.containsKey("role") && user != null) {
                    map.put("role", user.getRole());
                }
            } else {
                map.put("username", "System");
                if (!map.containsKey("role")) {
                    map.put("role", "SYSTEM");
                }
            }
            return map;
        }).collect(Collectors.toList());
        
        mapPage.setRecords(records);
        return mapPage;
    }

    @Override
    public void deleteAllLogs() {
        this.remove(new QueryWrapper<>());
    }

    @Override
    public void deleteOldLogs(int months) {
        LocalDateTime threshold = LocalDateTime.now().minusMonths(months);
        QueryWrapper<OperationLog> wrapper = new QueryWrapper<>();
        wrapper.lt("created_at", threshold);
        this.remove(wrapper);
    }
    
    // 每天凌晨 3 点执行清理任务，保留最近 3 个月的日志
    @Scheduled(cron = "0 0 3 * * ?")
    public void autoCleanLogs() {
        deleteOldLogs(3);
    }
}
