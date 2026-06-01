package com.gcky.durginoutsystem.exception;

import com.gcky.durginoutsystem.common.Result;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

/**
 * 全局异常处理器
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** 参数校验失败 — 返回 HTTP 400 + 字段级错误信息 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Result<String>> handleValidation(MethodArgumentNotValidException e) {
        String errors = e.getBindingResult().getFieldErrors().stream()
                .map(f -> f.getField() + ": " + f.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Result.error(400, errors));
    }

    /** 业务异常（如库存不足）— 返回 HTTP 400 + 业务消息 */
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Result<String>> handleRuntimeException(RuntimeException e) {
        log.warn("业务异常: {}", e.getMessage());
        String message = e.getMessage();
        if (message == null || message.isEmpty()) {
            message = "业务执行出错";
        }
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Result.error(400, message));
    }

    /** 未知系统异常 — 返回 HTTP 500，不泄露内部错误详情 */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Result<String>> handleException(Exception e) {
        log.error("系统内部异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Result.error(500, "系统内部错误，请联系管理员"));
    }
}
