package com.gcky.durginoutsystem.annotation;

import java.lang.annotation.*;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface Log {
    /**
     * 操作描述，例如："新增药品"、"用户登录"
     */
    String value() default "";
}
