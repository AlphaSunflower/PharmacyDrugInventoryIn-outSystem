package com.gcky.durginoutsystem.annotation;

import java.lang.annotation.*;

@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RequireRole {
    /** Allowed roles: ADMIN, DOCTOR, PHARMACIST */
    String[] value() default {};
}
