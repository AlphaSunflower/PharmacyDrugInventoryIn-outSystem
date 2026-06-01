package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("diagnosis_types")
public class DiagnosisType {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String remark;
}
