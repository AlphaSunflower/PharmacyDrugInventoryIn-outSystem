package com.gcky.durginoutsystem.entity.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;
import java.time.LocalDate;
import java.util.List;

@Data
public class VisitSubmitDTO {
    @NotBlank(message = "患者姓名不能为空")
    private String patientName;

    @NotBlank(message = "性别不能为空")
    private String gender;

    @NotNull(message = "年龄不能为空")
    @Positive(message = "年龄必须为正数")
    private Integer age;

    @NotNull(message = "就诊日期不能为空")
    private LocalDate visitDate;

    private Long diagnosisId;
    private String customDiagnosis;
    private String department;

    @NotEmpty(message = "药品列表不能为空")
    private List<VisitDrugDTO> drugs;

    @Data
    public static class VisitDrugDTO {
        @NotNull(message = "药品ID不能为空")
        private Long drugId;

        @NotNull(message = "数量不能为空")
        @Positive(message = "数量必须为正数")
        private Integer quantity;
    }
}
