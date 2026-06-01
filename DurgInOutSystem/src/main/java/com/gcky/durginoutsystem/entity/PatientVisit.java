package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("patient_visits")
public class PatientVisit {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long doctorId;
    private String patientName;
    private String gender;
    private Integer age;
    private Long diagnosisId;
    private String customDiagnosis; // 自定义诊断内容
    private String department; // 科室/部门
    private LocalDate visitDate;
    private String status; // DRAFT, SUBMITTED, RETURNED, COMPLETED
    private String returnReason;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
