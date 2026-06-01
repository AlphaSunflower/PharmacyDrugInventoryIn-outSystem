package com.gcky.durginoutsystem.entity.excel;

import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Data;

@Data
public class InventoryCheckExcel {
    @ExcelProperty("药品名称")
    private String drugName;

    @ExcelProperty("规格")
    private String drugSpec;

    @ExcelProperty("系统库存")
    private Integer systemStock;

    @ExcelProperty("实盘数量")
    private Integer actualStock;

    @ExcelProperty("差异")
    private Integer discrepancy;

    @ExcelProperty("备注")
    private String remark;
}
