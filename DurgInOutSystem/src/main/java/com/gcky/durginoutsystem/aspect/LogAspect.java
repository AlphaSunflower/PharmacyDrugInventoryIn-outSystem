package com.gcky.durginoutsystem.aspect;

import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.entity.OperationLog;
import com.gcky.durginoutsystem.service.OperationLogService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.User;

import java.time.LocalDateTime;
import java.util.Map;

@Aspect
@Component
@Slf4j
public class LogAspect {

    @Autowired
    private OperationLogService operationLogService;

    @Around("@annotation(logAnnotation)")
    public Object around(ProceedingJoinPoint point, Log logAnnotation) throws Throwable {
        Object result = point.proceed();

        try {
            saveLog(point, logAnnotation, result);
        } catch (Exception e) {
            log.error("记录操作日志失败", e);
        }

        return result;
    }

    private void saveLog(ProceedingJoinPoint point, Log logAnnotation, Object result) {
        OperationLog operationLog = new OperationLog();

        // 1. 设置操作描述
        String action = logAnnotation.value();
        if (action == null || action.isEmpty()) {
            MethodSignature signature = (MethodSignature) point.getSignature();
            action = signature.getMethod().getName();
        }
        operationLog.setAction(action);
        operationLog.setCreatedAt(LocalDateTime.now());

        // 2. 从 request attributes 获取用户信息 (由 AuthInterceptor 预解析)
        Long userId = null;
        String role = null;

        ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes != null) {
            HttpServletRequest request = attributes.getRequest();
            userId = (Long) request.getAttribute("userId");
            role = (String) request.getAttribute("role");
        }

        // 特殊处理：登录操作 (auth/login, auth/auto-login 没有经过拦截器，从返回值中提取)
        if (userId == null && result instanceof Result) {
            Result<?> r = (Result<?>) result;
            if (r.getCode() == 200 && r.getData() instanceof Map) {
                Map<?, ?> data = (Map<?, ?>) r.getData();
                Object userObj = data.get("user");
                if (userObj instanceof User u) {
                    userId = u.getId();
                    role = u.getRole();
                } else if (userObj instanceof Map) {
                    Map<?, ?> uMap = (Map<?, ?>) userObj;
                    Object idObj = uMap.get("id");
                    if (idObj != null) userId = Long.valueOf(idObj.toString());
                    Object roleObj = uMap.get("role");
                    if (roleObj != null) role = roleObj.toString();
                }
            }
        }

        operationLog.setUserId(userId);
        operationLog.setRole(role);

        // 3. 记录操作参数摘要
        try {
            Object[] args = point.getArgs();
            if (args != null && args.length > 0) {
                StringBuilder sb = new StringBuilder();
                for (Object arg : args) {
                    if (arg != null && !(arg instanceof jakarta.servlet.ServletRequest) && !(arg instanceof jakarta.servlet.ServletResponse)) {
                        sb.append(arg.toString()).append("; ");
                    }
                }
                String dataStr = sb.toString();
                if (dataStr.length() > 100) {
                    dataStr = dataStr.substring(0, 97) + "...";
                }
                operationLog.setOperateData(dataStr);
            }
        } catch (Exception e) {
            // 忽略参数解析错误
        }

        operationLogService.save(operationLog);
    }
}
