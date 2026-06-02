package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("purchase_plans")
public class PurchasePlan {
    @TableId(type = IdType.AUTO)
    private Long id;

    private String month;

    private String status;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
