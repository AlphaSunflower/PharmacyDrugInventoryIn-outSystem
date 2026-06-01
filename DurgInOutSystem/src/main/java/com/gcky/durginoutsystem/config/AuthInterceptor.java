package com.gcky.durginoutsystem.config;

import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.utils.JwtUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.security.SignatureException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Arrays;
import java.util.List;

@Slf4j
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Autowired
    private JwtUtil jwtUtil;

    private static final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // Skip non-handler requests (e.g., static resources)
        if (!(handler instanceof HandlerMethod handlerMethod)) {
            return true;
        }

        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            sendError(response, 401, "未登录或Token缺失");
            return false;
        }

        String token = authHeader.substring(7);

        try {
            Claims claims = jwtUtil.extractClaims(token);

            Long userId = claims.get("userId", Long.class);
            String role = claims.get("role", String.class);
            String username = claims.getSubject();

            if (userId == null || role == null) {
                sendError(response, 401, "Token无效：缺失用户信息");
                return false;
            }

            // Store extracted info in request attributes for controllers
            request.setAttribute("userId", userId);
            request.setAttribute("role", role);
            request.setAttribute("username", username);

            // Check @RequireRole annotation
            RequireRole requireRole = handlerMethod.getMethodAnnotation(RequireRole.class);
            if (requireRole == null) {
                requireRole = handlerMethod.getBeanType().getAnnotation(RequireRole.class);
            }

            if (requireRole != null && requireRole.value().length > 0) {
                List<String> allowedRoles = Arrays.asList(requireRole.value());
                if (!allowedRoles.contains(role)) {
                    sendError(response, 403, "无权限访问：需要角色 " + String.join(", ", allowedRoles));
                    return false;
                }
            }

            return true;

        } catch (ExpiredJwtException e) {
            sendError(response, 401, "Token已过期，请重新登录");
            return false;
        } catch (MalformedJwtException | SignatureException | IllegalArgumentException e) {
            sendError(response, 401, "Token无效");
            return false;
        }
    }

    private void sendError(HttpServletResponse response, int httpStatus, String message) throws Exception {
        response.setStatus(httpStatus);
        response.setContentType("application/json;charset=UTF-8");
        Result<String> result = Result.error(httpStatus, message);
        response.getWriter().write(objectMapper.writeValueAsString(result));
    }
}
