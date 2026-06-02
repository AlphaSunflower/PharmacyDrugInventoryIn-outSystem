package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@TableName("drugs")
public class Drug {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String spec;
    private String unit;
    private BigDecimal price;
    private Integer stockQuantity;
    private Integer isDeleted; // 0: no, 1: yes
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    @TableField(exist = false)
    private List<DrugBatch> batchList;

    @TableField(exist = false)
    private String manufacturer;
}
