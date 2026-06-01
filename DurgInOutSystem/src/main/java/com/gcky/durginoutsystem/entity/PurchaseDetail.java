package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("purchase_details")
public class PurchaseDetail {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long drugId;
    private Integer quantity;
    private String unit;
    private BigDecimal price;
    private BigDecimal totalAmount;
    private Long batchId;
    private LocalDate purchaseDate;
    private LocalDateTime createdAt;
}
