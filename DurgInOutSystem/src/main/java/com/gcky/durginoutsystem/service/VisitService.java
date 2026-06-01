package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.entity.dto.VisitSubmitDTO;

import java.util.Map;

public interface VisitService {
    void submitVisit(Long doctorId, VisitSubmitDTO visitDTO);
    Page<Map<String, Object>> getVisits(Integer page, Integer size, String status, Long doctorId, String keyword, String startDate, String endDate, Long diagnosisId, String department, String drugName);
    void dispense(Long visitId);
    void returnVisit(Long visitId, String reason);
    void updateVisit(Long visitId, VisitSubmitDTO visitDTO);
    void cancelVisit(Long visitId);
}
