package com.gcky.durginoutsystem.aspect;

import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.entity.OperationLog;
import com.gcky.durginoutsystem.service.OperationLogService;
import com.gcky.durginoutsystem.utils.JwtUtil;
import io.jsonwebtoken.Claims;
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

import java.time.LocalDateTime;

import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.User;
import java.util.Map;

@Aspect
@Component
@Slf4j
public class LogAspect {

    @Autowired
    private OperationLogService operationLogService;

    @Autowired
    private JwtUtil jwtUtil;

    @Around("@annotation(logAnnotation)")
    public Object around(ProceedingJoinPoint point, Log logAnnotation) throws Throwable {
        Object result = point.proceed(); // 执行目标方法

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

        // 2. 设置创建时间
        operationLog.setCreatedAt(LocalDateTime.now());

        // 3. 解析 Token 获取当前用户信息
        Map<String, Object> userInfo = getCurrentUserInfo();
        Long userId = userInfo != null ? (Long) userInfo.get("userId") : null;
        String role = userInfo != null ? (String) userInfo.get("role") : null;
        
        // 特殊处理：如果是登录操作且没有 Token (userId为null)，尝试从返回值中获取
        if (userId == null && result instanceof Result) {
             Result<?> r = (Result<?>) result;
             if (r.getCode() == 200 && r.getData() instanceof Map) {
                 Map<?, ?> data = (Map<?, ?>) r.getData();
                 if (data.containsKey("user")) {
                     Object userObj = data.get("user");
                     if (userObj instanceof User) {
                         User u = (User) userObj;
                         userId = u.getId();
                         role = u.getRole();
                     } else if (userObj instanceof Map) {
                         // 假如 User 被转成了 Map
                         Map<?, ?> uMap = (Map<?, ?>) userObj;
                         Object idObj = uMap.get("id");
                         if (idObj != null) userId = Long.valueOf(idObj.toString());
                         Object roleObj = uMap.get("role");
                         if (roleObj != null) role = roleObj.toString();
                     }
                 }
             }
        }
        
        operationLog.setUserId(userId);
        operationLog.setRole(role);
        
        // 4. 设置操作数据 (简单的参数记录)
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

        // 5. 保存到数据库
        operationLogService.save(operationLog);
    }

    private Map<String, Object> getCurrentUserInfo() {
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attributes == null) return null;

            HttpServletRequest request = attributes.getRequest();
            String authHeader = request.getHeader("Authorization");
            
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);
                Claims claims = jwtUtil.extractClaims(token);
                
                Map<String, Object> info = new java.util.HashMap<>();
                Object userIdObj = claims.get("userId");
                if (userIdObj != null) {
                     info.put("userId", Long.valueOf(userIdObj.toString()));
                }
                Object roleObj = claims.get("role");
                if (roleObj != null) {
                    info.put("role", roleObj.toString());
                }
                return info;
            }
        } catch (Exception e) {
            log.error("解析 Token 获取用户信息失败", e);
        }
        return null;
    }
}
