package com.gcky.durginoutsystem.controller;

import com.alibaba.excel.EasyExcel;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.*;
import com.gcky.durginoutsystem.entity.excel.DrugStatsExcel;
import com.gcky.durginoutsystem.entity.excel.OperationStatsExcel;
import com.gcky.durginoutsystem.entity.excel.WorkloadSummaryExcel;
import com.gcky.durginoutsystem.mapper.*;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole({"DOCTOR", "PHARMACIST"})
@RestController
@RequestMapping("/api/v1/stats")
public class StatsController {

    @Autowired
    private DrugMapper drugMapper;
    @Autowired
    private PatientVisitMapper visitMapper;
    @Autowired
    private VisitDrugMapper visitDrugMapper;
    @Autowired
    private PurchaseDetailMapper purchaseMapper;
    @Autowired
    private DiagnosisTypeMapper diagnosisTypeMapper;
    @Autowired
    private InventoryCheckTaskMapper inventoryTaskMapper;
    @Autowired
    private InventoryCheckDetailMapper inventoryDetailMapper;

    // 1. 就诊人数及药品费用消耗统计（按日统计，月度汇总）
    @GetMapping("/operations")
    public Result<Map<String, Object>> getOperationStats(@RequestParam String month) {
        return Result.success(calculateOperationStats(month));
    }

    // 导出运营报表
    @GetMapping("/operations/export")
    public void exportOperationStats(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = calculateOperationStats(month);
        List<Map<String, Object>> dailyStats = (List<Map<String, Object>>) stats.get("dailyStats");
        
        List<OperationStatsExcel> excelList = new ArrayList<>();
        for (Map<String, Object> map : dailyStats) {
            OperationStatsExcel vo = new OperationStatsExcel();
            vo.setDate((String) map.get("date"));
            vo.setVisits((Integer) map.get("visits"));
            vo.setTotalCost((BigDecimal) map.get("totalCost"));
            vo.setAvgCost((BigDecimal) map.get("avgCost"));
            vo.setDiagnosisDetails((String) map.get("diagnosisDetails"));
            excelList.add(vo);
        }

        // 添加汇总行
        Map<String, Object> summary = (Map<String, Object>) stats.get("summary");
        OperationStatsExcel sumVo = new OperationStatsExcel();
        sumVo.setDate("月度汇总");
        sumVo.setVisits((Integer) summary.get("totalVisits"));
        sumVo.setTotalCost((BigDecimal) summary.get("totalCost"));
        sumVo.setAvgCost((BigDecimal) summary.get("avgCost"));
        sumVo.setDiagnosisDetails("");
        excelList.add(sumVo);

        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String fileName = URLEncoder.encode("运营统计报表_" + month, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + fileName + ".xlsx");
        
        EasyExcel.write(response.getOutputStream(), OperationStatsExcel.class).sheet("运营统计").doWrite(excelList);
    }

    private Map<String, Object> calculateOperationStats(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);

        // 获取本月所有已完成或待发药的就诊记录
        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);

        // 获取相关的药品费用
        List<Long> visitIds = visits.stream().map(PatientVisit::getId).collect(Collectors.toList());
        List<VisitDrug> allVisitDrugs = new ArrayList<>();
        if (!visitIds.isEmpty()) {
            QueryWrapper<VisitDrug> vdWrapper = new QueryWrapper<>();
            vdWrapper.in("visit_id", visitIds);
            allVisitDrugs = visitDrugMapper.selectList(vdWrapper);
        }
        Map<Long, List<VisitDrug>> visitDrugMap = allVisitDrugs.stream()
                .collect(Collectors.groupingBy(VisitDrug::getVisitId));

        // 预加载诊断类型
        List<DiagnosisType> diagnosisTypes = diagnosisTypeMapper.selectList(null);
        Map<Long, String> diagnosisMap = diagnosisTypes.stream()
                .collect(Collectors.toMap(DiagnosisType::getId, DiagnosisType::getName));

        // 按日期分组
        Map<LocalDate, List<PatientVisit>> dailyVisits = visits.stream()
                .collect(Collectors.groupingBy(PatientVisit::getVisitDate));

        List<Map<String, Object>> dailyStats = new ArrayList<>();
        BigDecimal monthTotalCost = BigDecimal.ZERO;
        int monthTotalVisits = visits.size();

        for (LocalDate date = start; !date.isAfter(end); date = date.plusDays(1)) {
            if (date.isAfter(LocalDate.now())) break;

            List<PatientVisit> dayVisits = dailyVisits.getOrDefault(date, Collections.emptyList());
            int dayCount = dayVisits.size();
            
            BigDecimal dayCost = BigDecimal.ZERO;
            Map<String, Integer> dayDiagnosis = new HashMap<>();

            for (PatientVisit v : dayVisits) {
                List<VisitDrug> drugs = visitDrugMap.getOrDefault(v.getId(), Collections.emptyList());
                for (VisitDrug d : drugs) {
                    if (d.getAmount() != null) {
                        dayCost = dayCost.add(d.getAmount());
                    }
                }
                String diagName = diagnosisMap.getOrDefault(v.getDiagnosisId(), "未知");
                dayDiagnosis.put(diagName, dayDiagnosis.getOrDefault(diagName, 0) + 1);
            }

            monthTotalCost = monthTotalCost.add(dayCost);

            Map<String, Object> dayStat = new HashMap<>();
            dayStat.put("date", date.toString());
            dayStat.put("visits", dayCount);
            dayStat.put("totalCost", dayCost);
            dayStat.put("avgCost", dayCount > 0 ? dayCost.divide(BigDecimal.valueOf(dayCount), 2, RoundingMode.HALF_UP) : BigDecimal.ZERO);
            
            String diagStr = dayDiagnosis.entrySet().stream()
                    .map(e -> e.getKey() + " " + e.getValue() + "人")
                    .collect(Collectors.joining("，"));
            dayStat.put("diagnosisDetails", diagStr);

            dailyStats.add(dayStat);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("dailyStats", dailyStats);
        
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalVisits", monthTotalVisits);
        summary.put("totalCost", monthTotalCost);
        summary.put("avgCost", monthTotalVisits > 0 ? monthTotalCost.divide(BigDecimal.valueOf(monthTotalVisits), 2, RoundingMode.HALF_UP) : BigDecimal.ZERO);
        result.put("summary", summary);
        
        return result;
    }

    // 3. 月度汇总报表
    @GetMapping("/monthly-summary")
    public Result<Map<String, Object>> getMonthlySummary(@RequestParam String month) {
        return Result.success(calculateMonthlySummary(month));
    }

    // 导出月度汇总报表
    @GetMapping("/monthly-summary/export")
    public void exportMonthlySummary(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = calculateMonthlySummary(month);
        List<WorkloadSummaryExcel> excelList = buildWorkloadExcelList(stats);

        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String fileName = URLEncoder.encode("月度汇总报表_" + month, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + fileName + ".xlsx");
        
        EasyExcel.write(response.getOutputStream(), WorkloadSummaryExcel.class).sheet("月度汇总").doWrite(excelList);
    }

    private Map<String, Object> calculateMonthlySummary(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);
        String lastMonth = LocalDate.parse(month + "-01").minusMonths(1).toString().substring(0, 7);

        // 获取所有未删除的药品ID集合，用于过滤
        QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
        drugQuery.eq("is_deleted", 0);
        Set<Long> validDrugIds = drugMapper.selectList(drugQuery).stream()
                .map(Drug::getId)
                .collect(Collectors.toSet());

        // 1. 获取本月所有已完成或待发药的就诊记录
        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);

        // 2. 获取本月所有药品采购总金额
        QueryWrapper<PurchaseDetail> purchaseWrapper = new QueryWrapper<>();
        purchaseWrapper.between("purchase_date", start, end);
        List<PurchaseDetail> purchases = purchaseMapper.selectList(purchaseWrapper);
        BigDecimal purchaseTotalAmount = purchases.stream()
                .filter(p -> validDrugIds.contains(p.getDrugId())) // 过滤删除药品
                .map(PurchaseDetail::getTotalAmount)
                .filter(Objects::nonNull)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        // 3. 计算期初库存金额 (上个月盘点的期末金额)
        BigDecimal initialStockAmount = BigDecimal.ZERO;
        // isLastYearStockMissing 这里用于月度报表，指代上个月是否缺失
        boolean isLastMonthStockMissing = false;
        
        QueryWrapper<InventoryCheckTask> lastTaskWrapper = new QueryWrapper<>();
        lastTaskWrapper.eq("month", lastMonth);
        lastTaskWrapper.eq("status", "COMPLETED");
        InventoryCheckTask lastTask = inventoryTaskMapper.selectOne(lastTaskWrapper);
        if (lastTask != null) {
            QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
            detailWrapper.eq("task_id", lastTask.getId());
            List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(detailWrapper);
            
            // 优化：直接使用上月盘点明细中记录的 actualAmount
            // 如果旧数据没有 actualAmount，则回退到估算逻辑
            for (InventoryCheckDetail d : details) {
                if (!validDrugIds.contains(d.getDrugId())) continue; // 过滤删除药品

                if (d.getActualAmount() != null) {
                    initialStockAmount = initialStockAmount.add(d.getActualAmount());
                } else if (d.getActualStock() != null) {
                    // 回退逻辑：查当前药品价格 (不够精确但能用)
                    Drug drug = drugMapper.selectById(d.getDrugId());
                    if (drug != null) {
                        initialStockAmount = initialStockAmount.add(drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
                    }
                }
            }
        } else {
            isLastMonthStockMissing = true;
        }

        // 4. 计算期末库存金额 (本月盘点的期末金额)
        BigDecimal finalStockAmount = BigDecimal.ZERO;
        List<String> missingMonths = new ArrayList<>();
        
        QueryWrapper<InventoryCheckTask> currentTaskWrapper = new QueryWrapper<>();
        currentTaskWrapper.eq("month", month);
        currentTaskWrapper.eq("status", "COMPLETED");
        InventoryCheckTask currentTask = inventoryTaskMapper.selectOne(currentTaskWrapper);
        if (currentTask != null) {
            QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
            detailWrapper.eq("task_id", currentTask.getId());
            List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(detailWrapper);
            
            for (InventoryCheckDetail d : details) {
                if (!validDrugIds.contains(d.getDrugId())) continue; // 过滤删除药品

                if (d.getActualAmount() != null) {
                    finalStockAmount = finalStockAmount.add(d.getActualAmount());
                } else if (d.getActualStock() != null) {
                    Drug drug = drugMapper.selectById(d.getDrugId());
                    if (drug != null) {
                        finalStockAmount = finalStockAmount.add(drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
                    }
                }
            }
        } else {
            // 如果本月没盘点，记录
            if (LocalDate.parse(month + "-01").isBefore(LocalDate.now().withDayOfMonth(1)) || LocalDate.now().toString().startsWith(month)) {
                missingMonths.add(month);
            }
        }

        // 5. 领导拿药金额
        BigDecimal leaderAmount = BigDecimal.ZERO;
        List<PatientVisit> leaderVisits = visits.stream()
                .filter(v -> "领导拿药".equals(v.getDepartment()))
                .collect(Collectors.toList());
        if (!leaderVisits.isEmpty()) {
            List<Long> ids = leaderVisits.stream().map(PatientVisit::getId).collect(Collectors.toList());
            QueryWrapper<VisitDrug> vdWrapper = new QueryWrapper<>();
            vdWrapper.in("visit_id", ids);
            List<VisitDrug> vds = visitDrugMapper.selectList(vdWrapper);
            leaderAmount = vds.stream()
                    .filter(d -> validDrugIds.contains(d.getDrugId())) // 过滤删除药品
                    .map(VisitDrug::getAmount)
                    .filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        // 6. 构建行数据 (本厂, 外包)
        List<Map<String, Object>> rows = new ArrayList<>();
        
        // 预加载诊断类型名称用于判断“外伤”
        List<DiagnosisType> diagTypes = diagnosisTypeMapper.selectList(null);
        Map<Long, String> diagMap = diagTypes.stream().collect(Collectors.toMap(DiagnosisType::getId, DiagnosisType::getName));

        rows.add(buildDepartmentRow("本厂", visits, diagMap, validDrugIds));
        rows.add(buildDepartmentRow("外包", visits, diagMap, validDrugIds));

        Map<String, Object> result = new HashMap<>();
        result.put("rows", rows);
        result.put("initialStockAmount", initialStockAmount);
        result.put("purchaseTotalAmount", purchaseTotalAmount);
        result.put("finalStockAmount", finalStockAmount);
        result.put("leaderMedicineAmount", leaderAmount);
        result.put("isLastYearStockMissing", isLastMonthStockMissing); // 复用字段名保持一致
        result.put("missingInventoryMonths", missingMonths);

        return result;
    }

    private Map<String, Object> buildDepartmentRow(String deptName, List<PatientVisit> allVisits, Map<Long, String> diagMap, Set<Long> validDrugIds) {
        List<PatientVisit> deptVisits = allVisits.stream()
                .filter(v -> deptName.equals(v.getDepartment()))
                .collect(Collectors.toList());

        int visitCount = deptVisits.size();
        
        // 计算处方金额
        BigDecimal prescriptionAmount = BigDecimal.ZERO;
        BigDecimal traumaAmount = BigDecimal.ZERO;

        if (!deptVisits.isEmpty()) {
            List<Long> ids = deptVisits.stream().map(PatientVisit::getId).collect(Collectors.toList());
            QueryWrapper<VisitDrug> vdWrapper = new QueryWrapper<>();
            vdWrapper.in("visit_id", ids);
            List<VisitDrug> vds = visitDrugMapper.selectList(vdWrapper);
            
            // 按 VisitId 分组方便计算
            Map<Long, List<VisitDrug>> visitDrugMap = vds.stream().collect(Collectors.groupingBy(VisitDrug::getVisitId));

            for (PatientVisit v : deptVisits) {
                List<VisitDrug> drugs = visitDrugMap.getOrDefault(v.getId(), Collections.emptyList());
                BigDecimal visitTotal = drugs.stream()
                        .filter(d -> validDrugIds.contains(d.getDrugId())) // 过滤删除药品
                        .map(VisitDrug::getAmount)
                        .filter(Objects::nonNull)
                        .reduce(BigDecimal.ZERO, BigDecimal::add);
                
                prescriptionAmount = prescriptionAmount.add(visitTotal);

                // 判断外伤
                String dName = diagMap.getOrDefault(v.getDiagnosisId(), "");
                if (v.getCustomDiagnosis() != null) dName += v.getCustomDiagnosis();
                
                if (dName != null && dName.contains("外伤")) {
                    traumaAmount = traumaAmount.add(visitTotal);
                }
            }
        }

        Map<String, Object> row = new HashMap<>();
        row.put("department", deptName);
        row.put("visitCount", visitCount);
        row.put("prescriptionAmount", prescriptionAmount);
        row.put("traumaAmount", traumaAmount);
        return row;
    }

    // 4. 年度汇总报表
    @GetMapping("/yearly-summary")
    public Result<Map<String, Object>> getYearlySummary(@RequestParam String year) {
        return Result.success(calculateYearlySummary(year));
    }

    // 导出年度汇总报表
    @GetMapping("/yearly-summary/export")
    public void exportYearlySummary(@RequestParam String year, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = calculateYearlySummary(year);
        List<WorkloadSummaryExcel> excelList = buildWorkloadExcelList(stats);

        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String fileName = URLEncoder.encode("年度汇总报表_" + year, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + fileName + ".xlsx");
        
        EasyExcel.write(response.getOutputStream(), WorkloadSummaryExcel.class).sheet("年度汇总").doWrite(excelList);
    }

    private Map<String, Object> calculateYearlySummary(String year) {
        LocalDate start = LocalDate.parse(year + "-01-01");
        LocalDate end = LocalDate.parse(year + "-12-31");
        String lastYearMonth = (Integer.parseInt(year) - 1) + "-12"; // 上一年12月
        String currentYearMonth = year + "-12"; // 今年12月

        // 获取所有未删除的药品ID集合，用于过滤
        QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
        drugQuery.eq("is_deleted", 0);
        Set<Long> validDrugIds = drugMapper.selectList(drugQuery).stream()
                .map(Drug::getId)
                .collect(Collectors.toSet());

        // 1. 获取本年所有已完成或待发药的就诊记录
        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);

        // 2. 获取本年所有药品采购总金额
        QueryWrapper<PurchaseDetail> purchaseWrapper = new QueryWrapper<>();
        purchaseWrapper.between("purchase_date", start, end);
        List<PurchaseDetail> purchases = purchaseMapper.selectList(purchaseWrapper);
        BigDecimal purchaseTotalAmount = purchases.stream()
                .filter(p -> validDrugIds.contains(p.getDrugId())) // 过滤删除药品
                .map(PurchaseDetail::getTotalAmount)
                .filter(Objects::nonNull)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        // 3. 计算期初库存金额 (上一年12月盘点的期末金额)
        BigDecimal initialStockAmount = BigDecimal.ZERO;
        boolean isLastYearStockMissing = false;
        QueryWrapper<InventoryCheckTask> lastTaskWrapper = new QueryWrapper<>();
        lastTaskWrapper.eq("month", lastYearMonth);
        lastTaskWrapper.eq("status", "COMPLETED");
        InventoryCheckTask lastTask = inventoryTaskMapper.selectOne(lastTaskWrapper);
        if (lastTask != null) {
            QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
            detailWrapper.eq("task_id", lastTask.getId());
            List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(detailWrapper);
            
            for (InventoryCheckDetail d : details) {
                if (!validDrugIds.contains(d.getDrugId())) continue;

                if (d.getActualAmount() != null) {
                    initialStockAmount = initialStockAmount.add(d.getActualAmount());
                } else if (d.getActualStock() != null) {
                    Drug drug = drugMapper.selectById(d.getDrugId());
                    if (drug != null) {
                        initialStockAmount = initialStockAmount.add(drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
                    }
                }
            }
        } else {
            isLastYearStockMissing = true;
        }

        // 4. 计算期末库存金额 (累加本年每个月的期末实盘金额)
        BigDecimal finalStockAmount = BigDecimal.ZERO;
        List<String> missingMonths = new ArrayList<>();
        
        for (int m = 1; m <= 12; m++) {
            String monthStr = String.format("%s-%02d", year, m);
            // 如果月份还未到，跳过检查
            if (LocalDate.parse(monthStr + "-01").isAfter(LocalDate.now())) {
                continue;
            }
            
            QueryWrapper<InventoryCheckTask> taskWrapper = new QueryWrapper<>();
            taskWrapper.eq("month", monthStr);
            taskWrapper.eq("status", "COMPLETED");
            InventoryCheckTask task = inventoryTaskMapper.selectOne(taskWrapper);
            
            if (task != null) {
                QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
                detailWrapper.eq("task_id", task.getId());
                List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(detailWrapper);
                
                for (InventoryCheckDetail d : details) {
                    if (!validDrugIds.contains(d.getDrugId())) continue;

                    if (d.getActualAmount() != null) {
                        finalStockAmount = finalStockAmount.add(d.getActualAmount());
                    } else if (d.getActualStock() != null) {
                        Drug drug = drugMapper.selectById(d.getDrugId());
                        if (drug != null) {
                            finalStockAmount = finalStockAmount.add(drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
                        }
                    }
                }
            } else {
                // 如果当月已过但未盘点，记录缺失月份
                if (LocalDate.parse(monthStr + "-01").isBefore(LocalDate.now().withDayOfMonth(1))) {
                    missingMonths.add(monthStr);
                } else if (LocalDate.now().toString().startsWith(monthStr)) {
                    // 当前月也算缺失
                     missingMonths.add(monthStr);
                }
            }
        }

        // 5. 领导拿药金额
        BigDecimal leaderAmount = BigDecimal.ZERO;
        List<PatientVisit> leaderVisits = visits.stream()
                .filter(v -> "领导拿药".equals(v.getDepartment()))
                .collect(Collectors.toList());
        if (!leaderVisits.isEmpty()) {
            List<Long> ids = leaderVisits.stream().map(PatientVisit::getId).collect(Collectors.toList());
            QueryWrapper<VisitDrug> vdWrapper = new QueryWrapper<>();
            vdWrapper.in("visit_id", ids);
            List<VisitDrug> vds = visitDrugMapper.selectList(vdWrapper);
            leaderAmount = vds.stream()
                    .filter(d -> validDrugIds.contains(d.getDrugId()))
                    .map(VisitDrug::getAmount)
                    .filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        // 6. 构建行数据 (本厂, 外包)
        List<Map<String, Object>> rows = new ArrayList<>();
        
        List<DiagnosisType> diagTypes = diagnosisTypeMapper.selectList(null);
        Map<Long, String> diagMap = diagTypes.stream().collect(Collectors.toMap(DiagnosisType::getId, DiagnosisType::getName));

        rows.add(buildDepartmentRow("本厂", visits, diagMap, validDrugIds));
        rows.add(buildDepartmentRow("外包", visits, diagMap, validDrugIds));

        Map<String, Object> result = new HashMap<>();
        result.put("rows", rows);
        result.put("initialStockAmount", initialStockAmount);
        result.put("purchaseTotalAmount", purchaseTotalAmount);
        result.put("finalStockAmount", finalStockAmount);
        result.put("leaderMedicineAmount", leaderAmount);
        result.put("isLastYearStockMissing", isLastYearStockMissing);
        result.put("missingInventoryMonths", missingMonths);

        return result;
    }

    private List<WorkloadSummaryExcel> buildWorkloadExcelList(Map<String, Object> stats) {
        List<Map<String, Object>> rows = (List<Map<String, Object>>) stats.get("rows");
        List<WorkloadSummaryExcel> excelList = new ArrayList<>();
        
        BigDecimal leaderAmt = (BigDecimal) stats.get("leaderMedicineAmount");
        BigDecimal initStock = (BigDecimal) stats.get("initialStockAmount");
        BigDecimal purchaseAmt = (BigDecimal) stats.get("purchaseTotalAmount");
        BigDecimal finalStock = (BigDecimal) stats.get("finalStockAmount");

        for (int i = 0; i < rows.size(); i++) {
            Map<String, Object> row = rows.get(i);
            WorkloadSummaryExcel vo = new WorkloadSummaryExcel();
            vo.setDepartment((String) row.get("department"));
            vo.setVisitCount((Integer) row.get("visitCount"));
            vo.setPrescriptionAmount((BigDecimal) row.get("prescriptionAmount"));
            vo.setTraumaAmount((BigDecimal) row.get("traumaAmount"));
            
            // Only set global stats on the first row to simulate the merged cell effect
            if (i == 0) {
                vo.setLeaderMedicineAmount(leaderAmt);
                vo.setInitialStockAmount(initStock);
                vo.setPurchaseTotalAmount(purchaseAmt);
                vo.setFinalStockAmount(finalStock);
            }
            
            excelList.add(vo);
        }
        return excelList;
    }

    // 2. 药品购进与使用统计（按月统计）
    @GetMapping("/drugs")
    public Result<Map<String, Object>> getDrugStats(@RequestParam String month) {
        return Result.success(calculateDrugStats(month));
    }

    // 导出药品报表
    @GetMapping("/drugs/export")
    public void exportDrugStats(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = calculateDrugStats(month);
        List<Map<String, Object>> list = (List<Map<String, Object>>) stats.get("list");
        
        List<DrugStatsExcel> excelList = new ArrayList<>();
        for (Map<String, Object> map : list) {
            DrugStatsExcel vo = new DrugStatsExcel();
            vo.setDrugName((String) map.get("drugName"));
            vo.setSpec((String) map.get("spec"));
            vo.setStartStock((Integer) map.get("startStock"));
            vo.setStartAmount((BigDecimal) map.get("startAmount"));
            vo.setPurchaseQty((Integer) map.get("purchaseQty"));
            vo.setPurchaseUnit((String) map.get("purchaseUnit"));
            vo.setPurchasePrice((BigDecimal) map.get("purchasePrice"));
            vo.setPurchaseAmount((BigDecimal) map.get("purchaseAmount"));
            vo.setUseQty((Integer) map.get("useQty"));
            vo.setUseAmount((BigDecimal) map.get("useAmount"));
            vo.setEndTheoretical((Integer) map.get("endTheoretical"));
            vo.setEndActual((Integer) map.get("endActual"));
            vo.setEndAmount((BigDecimal) map.get("endAmount"));
            excelList.add(vo);
        }

        // 添加汇总行
        Map<String, Object> summary = (Map<String, Object>) stats.get("summary");
        DrugStatsExcel sumVo = new DrugStatsExcel();
        sumVo.setDrugName("合计");
        sumVo.setStartAmount((BigDecimal) summary.get("totalStartAmount"));
        sumVo.setPurchaseAmount((BigDecimal) summary.get("totalPurchaseAmount"));
        sumVo.setUseAmount((BigDecimal) summary.get("totalUseAmount"));
        sumVo.setEndAmount((BigDecimal) summary.get("totalEndAmount"));
        excelList.add(sumVo);

        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String fileName = URLEncoder.encode("药品进销存报表_" + month, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + fileName + ".xlsx");
        
        EasyExcel.write(response.getOutputStream(), DrugStatsExcel.class).sheet("药品进销存").doWrite(excelList);
    }

    private Map<String, Object> calculateDrugStats(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);
        String lastMonth = LocalDate.parse(month + "-01").minusMonths(1).toString().substring(0, 7);

        // 1. 获取所有药品 (过滤掉已删除的)
        QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
        drugQuery.eq("is_deleted", 0);
        List<Drug> allDrugs = drugMapper.selectList(drugQuery);

        // 2. 获取本月购进记录
        QueryWrapper<PurchaseDetail> purchaseWrapper = new QueryWrapper<>();
        purchaseWrapper.between("purchase_date", start, end);
        List<PurchaseDetail> monthPurchases = purchaseMapper.selectList(purchaseWrapper);
        Map<Long, List<PurchaseDetail>> purchaseMap = monthPurchases.stream()
                .collect(Collectors.groupingBy(PurchaseDetail::getDrugId));

        // 3. 获取本月使用记录 (关联 COMPLETED 状态的 Visit)
        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);
        List<Long> visitIds = visits.stream().map(PatientVisit::getId).collect(Collectors.toList());
        
        List<VisitDrug> monthUsages = new ArrayList<>();
        if (!visitIds.isEmpty()) {
            QueryWrapper<VisitDrug> vdWrapper = new QueryWrapper<>();
            vdWrapper.in("visit_id", visitIds);
            monthUsages = visitDrugMapper.selectList(vdWrapper);
        }
        Map<Long, List<VisitDrug>> usageMap = monthUsages.stream()
                .collect(Collectors.groupingBy(VisitDrug::getDrugId));

        // 4. 获取该月(期末)的盘点记录
        QueryWrapper<InventoryCheckTask> taskWrapper = new QueryWrapper<>();
        taskWrapper.eq("month", month);
        InventoryCheckTask checkTask = inventoryTaskMapper.selectOne(taskWrapper);
        boolean isCurrentMonthChecked = (checkTask != null && "COMPLETED".equals(checkTask.getStatus()));
        Map<Long, InventoryCheckDetail> checkDetailMap = new HashMap<>();
        if (isCurrentMonthChecked) {
            QueryWrapper<InventoryCheckDetail> detailWrapper = new QueryWrapper<>();
            detailWrapper.eq("task_id", checkTask.getId());
            List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(detailWrapper);
            checkDetailMap = details.stream().collect(Collectors.toMap(InventoryCheckDetail::getDrugId, d -> d));
        }

        // 5. 获取上月(期初)的盘点记录
        QueryWrapper<InventoryCheckTask> lastTaskWrapper = new QueryWrapper<>();
        lastTaskWrapper.eq("month", lastMonth);
        InventoryCheckTask lastCheckTask = inventoryTaskMapper.selectOne(lastTaskWrapper);
        boolean isStartStockMissing = (lastCheckTask == null || !"COMPLETED".equals(lastCheckTask.getStatus()));
        Map<Long, InventoryCheckDetail> lastCheckDetailMap = new HashMap<>();
        if (!isStartStockMissing) {
            QueryWrapper<InventoryCheckDetail> lastDetailWrapper = new QueryWrapper<>();
            lastDetailWrapper.eq("task_id", lastCheckTask.getId());
            List<InventoryCheckDetail> lastDetails = inventoryDetailMapper.selectList(lastDetailWrapper);
            lastCheckDetailMap = lastDetails.stream().collect(Collectors.toMap(InventoryCheckDetail::getDrugId, d -> d));
        }

        List<Map<String, Object>> drugStats = new ArrayList<>();
        BigDecimal totalStartAmt = BigDecimal.ZERO;
        BigDecimal totalPurchaseAmt = BigDecimal.ZERO;
        BigDecimal totalUsageAmt = BigDecimal.ZERO;
        BigDecimal totalEndAmt = BigDecimal.ZERO;

        for (Drug drug : allDrugs) {
            Long drugId = drug.getId();
            
            // A. 本月购进
            List<PurchaseDetail> myPurchases = purchaseMap.getOrDefault(drugId, Collections.emptyList());
            int purchaseQty = myPurchases.stream().mapToInt(PurchaseDetail::getQuantity).sum();
            BigDecimal purchaseAmt = myPurchases.stream()
                    .map(PurchaseDetail::getTotalAmount)
                    .filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            String unit = drug.getUnit();
            
            // 购进单价：取最新购进记录的单价，否则取 Drug 表参考价
            BigDecimal purchasePrice = drug.getPrice();
            if (!myPurchases.isEmpty()) {
                myPurchases.sort(Comparator.comparing(PurchaseDetail::getCreatedAt).reversed());
                purchasePrice = myPurchases.get(0).getPrice();
            }

            // B. 本月使用
            List<VisitDrug> myUsages = usageMap.getOrDefault(drugId, Collections.emptyList());
            int usageQty = myUsages.stream().mapToInt(VisitDrug::getQuantity).sum();
            BigDecimal usageAmt = myUsages.stream()
                    .map(VisitDrug::getAmount)
                    .filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);

            // C. 期初 (上月期末实盘)
            int startStock = 0;
            BigDecimal startAmt = BigDecimal.ZERO;
            if (!isStartStockMissing) {
                InventoryCheckDetail lastDetail = lastCheckDetailMap.get(drugId);
                if (lastDetail != null && lastDetail.getActualStock() != null) {
                    startStock = lastDetail.getActualStock();
                    // 优先使用记录的 actualAmount，如果旧数据没有，则用 actualStock * price 估算
                    if (lastDetail.getActualAmount() != null) {
                        startAmt = lastDetail.getActualAmount();
                    } else {
                        startAmt = drug.getPrice().multiply(new BigDecimal(startStock));
                    }
                }
            }

            // D. 期末
            int endTheoretical = 0;
            Integer endActual = null;
            BigDecimal endAmt = BigDecimal.ZERO;

            if (isCurrentMonthChecked) {
                InventoryCheckDetail detail = checkDetailMap.get(drugId);
                if (detail != null) {
                    endTheoretical = detail.getSystemStock(); // 盘点时的系统快照
                    endActual = detail.getActualStock();
                    if (detail.getActualAmount() != null) {
                        endAmt = detail.getActualAmount();
                    } else if (endActual != null) {
                        endAmt = drug.getPrice().multiply(new BigDecimal(endActual));
                    }
                }
            } else {
                // 如果本月还没盘点，期末理论 = 期初 + 购进 - 使用
                endTheoretical = startStock + purchaseQty - usageQty;
                // 期末实际为空
                // 期末金额暂按理论值预估
                endAmt = drug.getPrice().multiply(new BigDecimal(endTheoretical));
            }

            // 汇总
            totalStartAmt = totalStartAmt.add(startAmt);
            totalPurchaseAmt = totalPurchaseAmt.add(purchaseAmt);
            totalUsageAmt = totalUsageAmt.add(usageAmt);
            totalEndAmt = totalEndAmt.add(endAmt);

            Map<String, Object> row = new HashMap<>();
            row.put("drugId", drugId);
            row.put("drugName", drug.getName());
            row.put("spec", drug.getSpec());
            
            row.put("startStock", startStock);
            row.put("startAmount", startAmt);
            
            row.put("purchaseQty", purchaseQty);
            row.put("purchaseUnit", unit);
            row.put("purchasePrice", purchasePrice);
            row.put("purchaseAmount", purchaseAmt);
            
            row.put("useQty", usageQty);
            row.put("useAmount", usageAmt);
            
            row.put("endTheoretical", endTheoretical);
            row.put("endActual", endActual);
            row.put("endAmount", endAmt);
            
            drugStats.add(row);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("list", drugStats);
        
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalStartAmount", totalStartAmt);
        summary.put("totalPurchaseAmount", totalPurchaseAmt);
        summary.put("totalUseAmount", totalUsageAmt);
        summary.put("totalEndAmount", totalEndAmt);
        result.put("summary", summary);
        
        // 标记信息，供前端展示红字或弹窗
        result.put("isStartStockMissing", isStartStockMissing);
        result.put("isCurrentMonthChecked", isCurrentMonthChecked);
        
        return result;
    }
}
