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
        
        Page<Map<String, Object>> mapPage = new Page<>(page, size, resultPage.getTotal());
        
        List<Map<String, Object>> records = resultPage.getRecords().stream().map(log -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", log.getId());
            map.put("action", log.getAction());
            map.put("createdAt", log.getCreatedAt());
            map.put("userId", log.getUserId());
            map.put("operateData", log.getOperateData());
            
            // 优先使用日志快照中的角色
            if (log.getRole() != null) {
                map.put("role", log.getRole());
            }

            if (log.getUserId() != null) {
                User user = userMapper.selectById(log.getUserId());
                map.put("username", user != null ? user.getUsername() : "Unknown");
                // 如果日志中没有角色，尝试从当前用户表中获取
                if (!map.containsKey("role")) {
                    map.put("role", user != null ? user.getRole() : "");
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
