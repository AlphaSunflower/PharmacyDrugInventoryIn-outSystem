package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;

@Data
@TableName("inventory_check_details")
public class InventoryCheckDetail {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private Long drugId;
    private Integer systemStock;
    private Integer actualStock;
    private BigDecimal actualAmount; // 期末实盘金额
    private Integer discrepancy;
    private String remark;
}
