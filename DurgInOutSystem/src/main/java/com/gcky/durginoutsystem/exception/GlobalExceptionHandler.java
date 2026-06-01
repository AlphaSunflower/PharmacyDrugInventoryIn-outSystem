package com.gcky.durginoutsystem.exception;

import com.gcky.durginoutsystem.common.Result;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /**
     * 处理所有未捕获的异常
     */
    @ExceptionHandler(Exception.class)
    public Result<String> handleException(Exception e) {
        log.error("系统内部异常", e);
        // 对于未知的系统异常，不直接返回堆栈信息给前端，而是返回通用错误提示，避免敏感信息泄露
        // 但为了满足用户"操作失败：（message信息）"的需求，如果是 RuntimeException 且有 message，我们尽量返回 message
        String message = e.getMessage();
        if (message == null || message.isEmpty()) {
            message = "系统内部错误";
        }
        return Result.error(500, message);
    }

    /**
     * 处理运行时异常（通常是业务逻辑检查抛出的，如"库存不足"）
     */
    @ExceptionHandler(RuntimeException.class)
    public Result<String> handleRuntimeException(RuntimeException e) {
        log.error("业务运行时异常", e);
        String message = e.getMessage();
        if (message == null || message.isEmpty()) {
            message = "业务执行出错";
        }
        return Result.error(500, message);
    }
}
