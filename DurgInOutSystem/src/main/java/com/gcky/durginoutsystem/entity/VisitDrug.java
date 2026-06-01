package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.math.BigDecimal;

@Data
@TableName("visit_drugs")
public class VisitDrug {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long visitId;
    private Long drugId;
    private Integer quantity;
    private BigDecimal amount;
    // batch_id 已废弃，不再绑定具体批次
    // price 字段可以保留作为“成交单价”记录，方便后续统计和退费计算，建议保留
    private BigDecimal price; 
}
