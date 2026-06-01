package com.gcky.durginoutsystem.entity.excel;

import com.alibaba.excel.annotation.ExcelProperty;
import com.alibaba.excel.annotation.write.style.ColumnWidth;
import lombok.Data;
import java.math.BigDecimal;

@Data
public class WorkloadSummaryExcel {
    @ExcelProperty("部门")
    @ColumnWidth(15)
    private String department;

    @ExcelProperty("接诊人数")
    private Integer visitCount;

    @ExcelProperty("处方开出金额")
    private BigDecimal prescriptionAmount;

    @ExcelProperty("外伤处理金额")
    private BigDecimal traumaAmount;

    @ExcelProperty("领导拿药金额")
    @ColumnWidth(15)
    private BigDecimal leaderMedicineAmount;

    @ExcelProperty("期初库存金额")
    @ColumnWidth(15)
    private BigDecimal initialStockAmount;

    @ExcelProperty("药品采购总金额")
    @ColumnWidth(15)
    private BigDecimal purchaseTotalAmount;

    @ExcelProperty("期末库存金额")
    @ColumnWidth(15)
    private BigDecimal finalStockAmount;
}
