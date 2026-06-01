package com.gcky.durginoutsystem.service;

import java.util.List;
import java.util.Map;

public interface StatsService {
    Map<String, Object> calculateOperationStats(String month);
    Map<String, Object> calculateDrugStats(String month);
    Map<String, Object> calculateMonthlySummary(String month);
    Map<String, Object> calculateYearlySummary(String year);
    List<Map<String, Object>> buildWorkloadExcelList(Map<String, Object> stats);
    Map<String, Object> getInventoryCheckReport(String month);
}
