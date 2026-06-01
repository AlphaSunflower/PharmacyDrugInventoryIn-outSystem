package com.gcky.durginoutsystem.exception;

/**
 * 业务异常 — 用于表示"库存不足"、"状态不正确"等可预期的业务错误。
 * 由 GlobalExceptionHandler 统一捕获，返回 HTTP 400 + 业务消息给前端。
 */
public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
}
