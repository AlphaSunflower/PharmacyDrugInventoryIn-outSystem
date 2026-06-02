package com.gcky.durginoutsystem.service;

import java.util.List;
import java.util.Map;

public interface PurchasePlanService {
    Long generatePlan(String month);
    List<Map<String, Object>> getPlanDetails(Long planId);
    void updateDetail(Long detailId, Integer plannedQuantity, String manufacturer);
    void completePlan(Long planId);
    void reopenPlan(Long planId);
    void deletePlan(Long planId);
}
