package com.gcky.durginoutsystem.entity.excel;

import com.alibaba.excel.annotation.ExcelProperty;
import com.alibaba.excel.annotation.write.style.ColumnWidth;
import lombok.Data;
import java.math.BigDecimal;

@Data
public class DrugStatsExcel {
    @ExcelProperty("药品名称")
    @ColumnWidth(20)
    private String drugName;

    @ExcelProperty("规格")
    @ColumnWidth(15)
    private String spec;

    @ExcelProperty("期初数量")
    private Integer startStock;

    @ExcelProperty("期初金额")
    private BigDecimal startAmount;

    @ExcelProperty("本月购进")
    private Integer purchaseQty;

    @ExcelProperty("单位")
    private String purchaseUnit;

    @ExcelProperty("购进单价")
    private BigDecimal purchasePrice;

    @ExcelProperty("购进金额")
    private BigDecimal purchaseAmount;

    @ExcelProperty("本月使用")
    private Integer useQty;

    @ExcelProperty("使用金额")
    private BigDecimal useAmount;

    @ExcelProperty("期末理论")
    private Integer endTheoretical;

    @ExcelProperty("期末实盘")
    private Integer endActual;

    @ExcelProperty("期末金额")
    private BigDecimal endAmount;
}
