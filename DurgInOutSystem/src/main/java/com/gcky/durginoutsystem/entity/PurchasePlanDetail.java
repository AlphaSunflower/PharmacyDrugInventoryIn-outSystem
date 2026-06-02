package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("purchase_plan_details")
public class PurchasePlanDetail {
    @TableId(type = IdType.AUTO)
    private Long id;

    private Long planId;

    private Long drugId;

    private String spec;

    private String unit;

    private BigDecimal purchasePrice;

    private String manufacturer;

    private Integer plannedQuantity;

    private LocalDateTime createdAt;
}
