package com.gcky.durginoutsystem.entity.excel;

import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class PurchasePlanExcel {
    @ExcelProperty("药品名称")
    private String drugName;

    @ExcelProperty("规格")
    private String spec;

    @ExcelProperty("单位")
    private String unit;

    @ExcelProperty("计划数量")
    private Integer plannedQuantity;

    @ExcelProperty("进货价")
    private BigDecimal purchasePrice;

    @ExcelProperty("生产厂家")
    private String manufacturer;
}
