package com.gcky.durginoutsystem.entity.dto;

import lombok.Data;
import java.time.LocalDate;
import java.util.List;

@Data
public class VisitSubmitDTO {
    private String patientName;
    private String gender;
    private Integer age;
    private LocalDate visitDate;
    private Long diagnosisId;
    private String customDiagnosis;
    private String department;
    private List<VisitDrugDTO> drugs;

    @Data
    public static class VisitDrugDTO {
        private Long drugId;
        private Integer quantity;
    }
}
