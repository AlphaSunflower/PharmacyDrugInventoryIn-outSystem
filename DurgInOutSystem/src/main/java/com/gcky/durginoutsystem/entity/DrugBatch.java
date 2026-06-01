package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("drug_batches")
public class DrugBatch {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long drugId;
    
    private String batchNo;
    
    private BigDecimal price;
    
    private Integer stockQuantity;
    
    private Integer initialQuantity;
    
    private LocalDate productionDate;
    
    private LocalDate expiryDate;
    
    private LocalDateTime createdAt;
}
