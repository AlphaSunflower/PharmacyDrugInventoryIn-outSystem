package com.gcky.durginoutsystem.entity.excel;

import com.alibaba.excel.annotation.ExcelProperty;
import com.alibaba.excel.annotation.write.style.ColumnWidth;
import lombok.Data;
import java.math.BigDecimal;

@Data
public class OperationStatsExcel {
    @ExcelProperty("日期")
    @ColumnWidth(15)
    private String date;

    @ExcelProperty("就诊人数")
    private Integer visits;

    @ExcelProperty("药品费用")
    private BigDecimal totalCost;

    @ExcelProperty("人均费用")
    private BigDecimal avgCost;

    @ExcelProperty("诊治分类统计")
    @ColumnWidth(50)
    private String diagnosisDetails;
}
