package com.gcky.durginoutsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.*;
import com.gcky.durginoutsystem.mapper.*;
import com.gcky.durginoutsystem.service.StatsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class StatsServiceImpl implements StatsService {

    @Autowired private DrugMapper drugMapper;
    @Autowired private PatientVisitMapper visitMapper;
    @Autowired private VisitDrugMapper visitDrugMapper;
    @Autowired private PurchaseDetailMapper purchaseMapper;
    @Autowired private DiagnosisTypeMapper diagnosisTypeMapper;
    @Autowired private InventoryCheckTaskMapper inventoryTaskMapper;
    @Autowired private InventoryCheckDetailMapper inventoryDetailMapper;

    // ==================== 药品进销存月报 ====================

    @Override
    public Map<String, Object> calculateDrugStats(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);
        String lastMonth = start.minusMonths(1).toString().substring(0, 7);

        QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
        drugQuery.eq("is_deleted", 0);
        List<Drug> allDrugs = drugMapper.selectList(drugQuery);

        QueryWrapper<PurchaseDetail> purchaseWrapper = new QueryWrapper<>();
        purchaseWrapper.between("purchase_date", start, end);
        List<PurchaseDetail> monthPurchases = purchaseMapper.selectList(purchaseWrapper);
        Map<Long, List<PurchaseDetail>> purchaseMap = monthPurchases.stream()
                .collect(Collectors.groupingBy(PurchaseDetail::getDrugId));

        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);
        List<Long> visitIds = visits.stream().map(PatientVisit::getId).collect(Collectors.toList());

        List<VisitDrug> monthUsages = new ArrayList<>();
        if (!visitIds.isEmpty()) {
            monthUsages = visitDrugMapper.selectList(
                    new QueryWrapper<VisitDrug>().in("visit_id", visitIds));
        }
        Map<Long, List<VisitDrug>> usageMap = monthUsages.stream()
                .collect(Collectors.groupingBy(VisitDrug::getDrugId));

        InventoryCheckTask checkTask = inventoryTaskMapper.selectOne(
                new QueryWrapper<InventoryCheckTask>().eq("month", month));
        boolean isCurrentMonthChecked = (checkTask != null && "COMPLETED".equals(checkTask.getStatus()));
        Map<Long, InventoryCheckDetail> checkDetailMap = new HashMap<>();
        if (isCurrentMonthChecked) {
            checkDetailMap = inventoryDetailMapper.selectList(
                    new QueryWrapper<InventoryCheckDetail>().eq("task_id", checkTask.getId()))
                    .stream().collect(Collectors.toMap(InventoryCheckDetail::getDrugId, d -> d));
        }

        InventoryCheckTask lastCheckTask = inventoryTaskMapper.selectOne(
                new QueryWrapper<InventoryCheckTask>().eq("month", lastMonth));
        boolean isStartStockMissing = (lastCheckTask == null || !"COMPLETED".equals(lastCheckTask.getStatus()));
        Map<Long, InventoryCheckDetail> lastCheckDetailMap = new HashMap<>();
        if (!isStartStockMissing) {
            lastCheckDetailMap = inventoryDetailMapper.selectList(
                    new QueryWrapper<InventoryCheckDetail>().eq("task_id", lastCheckTask.getId()))
                    .stream().collect(Collectors.toMap(InventoryCheckDetail::getDrugId, d -> d));
        }

        List<Map<String, Object>> drugStats = new ArrayList<>();
        BigDecimal totalStartAmt = BigDecimal.ZERO, totalPurchaseAmt = BigDecimal.ZERO,
                totalUsageAmt = BigDecimal.ZERO, totalEndAmt = BigDecimal.ZERO;

        for (Drug drug : allDrugs) {
            Long drugId = drug.getId();
            List<PurchaseDetail> myPurchases = purchaseMap.getOrDefault(drugId, Collections.emptyList());
            int purchaseQty = myPurchases.stream().mapToInt(PurchaseDetail::getQuantity).sum();
            BigDecimal purchaseAmt = myPurchases.stream().map(PurchaseDetail::getTotalAmount)
                    .filter(Objects::nonNull).reduce(BigDecimal.ZERO, BigDecimal::add);

            BigDecimal purchasePrice = drug.getPrice();
            if (!myPurchases.isEmpty()) {
                myPurchases.sort(Comparator.comparing(PurchaseDetail::getCreatedAt).reversed());
                purchasePrice = myPurchases.get(0).getPrice();
            }

            List<VisitDrug> myUsages = usageMap.getOrDefault(drugId, Collections.emptyList());
            int usageQty = myUsages.stream().mapToInt(VisitDrug::getQuantity).sum();
            BigDecimal usageAmt = myUsages.stream().map(VisitDrug::getAmount)
                    .filter(Objects::nonNull).reduce(BigDecimal.ZERO, BigDecimal::add);

            int startStock = 0;
            BigDecimal startAmt = BigDecimal.ZERO;
            if (!isStartStockMissing) {
                InventoryCheckDetail lastDetail = lastCheckDetailMap.get(drugId);
                if (lastDetail != null && lastDetail.getActualStock() != null) {
                    startStock = lastDetail.getActualStock();
                    startAmt = lastDetail.getActualAmount() != null
                            ? lastDetail.getActualAmount()
                            : drug.getPrice().multiply(new BigDecimal(startStock));
                }
            }

            int endTheoretical;
            Integer endActual = null;
            BigDecimal endAmt = BigDecimal.ZERO;
            if (isCurrentMonthChecked) {
                InventoryCheckDetail detail = checkDetailMap.get(drugId);
                if (detail != null) {
                    endTheoretical = detail.getSystemStock();
                    endActual = detail.getActualStock();
                    endAmt = detail.getActualAmount() != null
                            ? detail.getActualAmount()
                            : (endActual != null ? drug.getPrice().multiply(new BigDecimal(endActual)) : BigDecimal.ZERO);
                } else {
                    endTheoretical = startStock + purchaseQty - usageQty;
                }
            } else {
                endTheoretical = startStock + purchaseQty - usageQty;
                endAmt = drug.getPrice().multiply(new BigDecimal(endTheoretical));
            }

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
            row.put("purchaseUnit", drug.getUnit());
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
        result.put("isStartStockMissing", isStartStockMissing);
        result.put("isCurrentMonthChecked", isCurrentMonthChecked);
        return result;
    }

    // ==================== 运营统计月报 ====================

    @Override
    public Map<String, Object> calculateOperationStats(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);

        QueryWrapper<PatientVisit> visitWrapper = new QueryWrapper<>();
        visitWrapper.between("visit_date", start, end);
        visitWrapper.eq("status", "COMPLETED");
        List<PatientVisit> visits = visitMapper.selectList(visitWrapper);

        List<Long> visitIds = visits.stream().map(PatientVisit::getId).collect(Collectors.toList());
        List<VisitDrug> allVisitDrugs = new ArrayList<>();
        if (!visitIds.isEmpty()) {
            allVisitDrugs = visitDrugMapper.selectList(new QueryWrapper<VisitDrug>().in("visit_id", visitIds));
        }
        Map<Long, List<VisitDrug>> visitDrugMap = allVisitDrugs.stream()
                .collect(Collectors.groupingBy(VisitDrug::getVisitId));

        List<DiagnosisType> diagnosisTypes = diagnosisTypeMapper.selectList(null);
        Map<Long, String> diagnosisMap = diagnosisTypes.stream()
                .collect(Collectors.toMap(DiagnosisType::getId, DiagnosisType::getName));

        Map<LocalDate, List<PatientVisit>> dailyVisits = visits.stream()
                .collect(Collectors.groupingBy(PatientVisit::getVisitDate));

        List<Map<String, Object>> dailyStats = new ArrayList<>();
        BigDecimal monthTotalCost = BigDecimal.ZERO;

        for (LocalDate date = start; !date.isAfter(end); date = date.plusDays(1)) {
            if (date.isAfter(LocalDate.now())) break;
            List<PatientVisit> dayVisits = dailyVisits.getOrDefault(date, Collections.emptyList());
            int dayCount = dayVisits.size();
            BigDecimal dayCost = BigDecimal.ZERO;
            Map<String, Integer> dayDiagnosis = new HashMap<>();

            for (PatientVisit v : dayVisits) {
                List<VisitDrug> drugs = visitDrugMap.getOrDefault(v.getId(), Collections.emptyList());
                for (VisitDrug d : drugs) {
                    if (d.getAmount() != null) dayCost = dayCost.add(d.getAmount());
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
            dayStat.put("diagnosisDetails", dayDiagnosis.entrySet().stream()
                    .map(e -> e.getKey() + " " + e.getValue() + "人").collect(Collectors.joining("，")));
            dailyStats.add(dayStat);
        }

        int monthTotalVisits = visits.size();
        Map<String, Object> result = new HashMap<>();
        result.put("dailyStats", dailyStats);
        Map<String, Object> summary = new HashMap<>();
        summary.put("totalVisits", monthTotalVisits);
        summary.put("totalCost", monthTotalCost);
        summary.put("avgCost", monthTotalVisits > 0
                ? monthTotalCost.divide(BigDecimal.valueOf(monthTotalVisits), 2, RoundingMode.HALF_UP) : BigDecimal.ZERO);
        result.put("summary", summary);
        return result;
    }

    // ==================== 月度 / 年度汇总（共享核心逻辑）====================

    @Override
    public Map<String, Object> calculateMonthlySummary(String month) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);
        String prevPeriod = start.minusMonths(1).toString().substring(0, 7);
        return calculateSummaryReport(start, end, month, prevPeriod, false);
    }

    @Override
    public Map<String, Object> calculateYearlySummary(String year) {
        LocalDate start = LocalDate.parse(year + "-01-01");
        LocalDate end = LocalDate.parse(year + "-12-31");
        String prevPeriod = (Integer.parseInt(year) - 1) + "-12";
        return calculateSummaryReport(start, end, year, prevPeriod, true);
    }

    /** 月度/年度汇总报表共享逻辑 */
    private Map<String, Object> calculateSummaryReport(LocalDate start, LocalDate end,
                                                        String periodKey, String prevPeriod, boolean isYearly) {
        Set<Long> validDrugIds = drugMapper.selectList(
                new QueryWrapper<Drug>().eq("is_deleted", 0)).stream()
                .map(Drug::getId).collect(Collectors.toSet());

        // 就诊记录
        List<PatientVisit> visits = visitMapper.selectList(
                new QueryWrapper<PatientVisit>().between("visit_date", start, end).eq("status", "COMPLETED"));

        // 采购总额
        BigDecimal purchaseTotalAmount = purchaseMapper.selectList(
                new QueryWrapper<PurchaseDetail>().between("purchase_date", start, end)).stream()
                .filter(p -> validDrugIds.contains(p.getDrugId()))
                .map(PurchaseDetail::getTotalAmount).filter(Objects::nonNull)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        // 期初库存
        BigDecimal initialStockAmount = BigDecimal.ZERO;
        boolean isPrevStockMissing = false;
        InventoryCheckTask prevTask = inventoryTaskMapper.selectOne(
                new QueryWrapper<InventoryCheckTask>().eq("month", prevPeriod).eq("status", "COMPLETED"));
        if (prevTask != null) {
            for (InventoryCheckDetail d : inventoryDetailMapper.selectList(
                    new QueryWrapper<InventoryCheckDetail>().eq("task_id", prevTask.getId()))) {
                if (!validDrugIds.contains(d.getDrugId())) continue;
                if (d.getActualAmount() != null) {
                    initialStockAmount = initialStockAmount.add(d.getActualAmount());
                } else if (d.getActualStock() != null) {
                    Drug drug = drugMapper.selectById(d.getDrugId());
                    if (drug != null) initialStockAmount = initialStockAmount.add(
                            drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
                }
            }
        } else {
            isPrevStockMissing = true;
        }

        // 期末库存
        BigDecimal finalStockAmount = BigDecimal.ZERO;
        List<String> missingMonths = new ArrayList<>();
        if (isYearly) {
            // 取最近一个完成盘点月份的期末金额
            for (int m = 12; m >= 1; m--) {
                String mStr = String.format("%s-%02d", periodKey, m);
                if (LocalDate.parse(mStr + "-01").isAfter(LocalDate.now())) continue;
                InventoryCheckTask task = inventoryTaskMapper.selectOne(
                        new QueryWrapper<InventoryCheckTask>().eq("month", mStr).eq("status", "COMPLETED"));
                if (task != null) {
                    finalStockAmount = sumActualAmount(task.getId(), validDrugIds);
                    break;
                }
            }
            for (int m = 1; m <= 12; m++) {
                String mStr = String.format("%s-%02d", periodKey, m);
                if (LocalDate.parse(mStr + "-01").isAfter(LocalDate.now())) continue;
                if (inventoryTaskMapper.selectCount(
                        new QueryWrapper<InventoryCheckTask>().eq("month", mStr).eq("status", "COMPLETED")) == 0) {
                    missingMonths.add(mStr);
                }
            }
        } else {
            InventoryCheckTask curTask = inventoryTaskMapper.selectOne(
                    new QueryWrapper<InventoryCheckTask>().eq("month", periodKey).eq("status", "COMPLETED"));
            if (curTask != null) {
                finalStockAmount = sumActualAmount(curTask.getId(), validDrugIds);
            } else if (start.isBefore(LocalDate.now().withDayOfMonth(1))
                    || LocalDate.now().toString().startsWith(periodKey)) {
                missingMonths.add(periodKey);
            }
        }

        // 领导拿药
        BigDecimal leaderAmount = BigDecimal.ZERO;
        List<PatientVisit> leaderVisits = visits.stream()
                .filter(v -> "领导拿药".equals(v.getDepartment())).collect(Collectors.toList());
        if (!leaderVisits.isEmpty()) {
            List<Long> ids = leaderVisits.stream().map(PatientVisit::getId).collect(Collectors.toList());
            leaderAmount = visitDrugMapper.selectList(new QueryWrapper<VisitDrug>().in("visit_id", ids)).stream()
                    .filter(d -> validDrugIds.contains(d.getDrugId()))
                    .map(VisitDrug::getAmount).filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
        }

        // 部门行
        List<DiagnosisType> diagTypes = diagnosisTypeMapper.selectList(null);
        Map<Long, String> diagMap = diagTypes.stream().collect(Collectors.toMap(DiagnosisType::getId, DiagnosisType::getName));
        List<Map<String, Object>> rows = new ArrayList<>();
        rows.add(buildDepartmentRow("本厂", visits, diagMap, validDrugIds));
        rows.add(buildDepartmentRow("外包", visits, diagMap, validDrugIds));

        Map<String, Object> result = new HashMap<>();
        result.put("rows", rows);
        result.put("initialStockAmount", initialStockAmount);
        result.put("purchaseTotalAmount", purchaseTotalAmount);
        result.put("finalStockAmount", finalStockAmount);
        result.put("leaderMedicineAmount", leaderAmount);
        result.put("isLastYearStockMissing", isPrevStockMissing);
        result.put("missingInventoryMonths", missingMonths);
        return result;
    }

    private BigDecimal sumActualAmount(Long taskId, Set<Long> validDrugIds) {
        BigDecimal total = BigDecimal.ZERO;
        for (InventoryCheckDetail d : inventoryDetailMapper.selectList(
                new QueryWrapper<InventoryCheckDetail>().eq("task_id", taskId))) {
            if (!validDrugIds.contains(d.getDrugId())) continue;
            if (d.getActualAmount() != null) {
                total = total.add(d.getActualAmount());
            } else if (d.getActualStock() != null) {
                Drug drug = drugMapper.selectById(d.getDrugId());
                if (drug != null) total = total.add(drug.getPrice().multiply(new BigDecimal(d.getActualStock())));
            }
        }
        return total;
    }

    private Map<String, Object> buildDepartmentRow(String deptName, List<PatientVisit> allVisits,
                                                    Map<Long, String> diagMap, Set<Long> validDrugIds) {
        List<PatientVisit> deptVisits = allVisits.stream()
                .filter(v -> deptName.equals(v.getDepartment())).collect(Collectors.toList());
        int visitCount = deptVisits.size();
        BigDecimal prescriptionAmount = BigDecimal.ZERO, traumaAmount = BigDecimal.ZERO;

        if (!deptVisits.isEmpty()) {
            List<Long> ids = deptVisits.stream().map(PatientVisit::getId).collect(Collectors.toList());
            Map<Long, List<VisitDrug>> visitDrugMap = visitDrugMapper.selectList(
                    new QueryWrapper<VisitDrug>().in("visit_id", ids)).stream()
                    .collect(Collectors.groupingBy(VisitDrug::getVisitId));

            for (PatientVisit v : deptVisits) {
                List<VisitDrug> drugs = visitDrugMap.getOrDefault(v.getId(), Collections.emptyList());
                BigDecimal visitTotal = drugs.stream()
                        .filter(d -> validDrugIds.contains(d.getDrugId()))
                        .map(VisitDrug::getAmount).filter(Objects::nonNull)
                        .reduce(BigDecimal.ZERO, BigDecimal::add);
                prescriptionAmount = prescriptionAmount.add(visitTotal);

                String dName = diagMap.getOrDefault(v.getDiagnosisId(), "");
                if (v.getCustomDiagnosis() != null) dName += v.getCustomDiagnosis();
                if (dName.contains("外伤")) traumaAmount = traumaAmount.add(visitTotal);
            }
        }

        Map<String, Object> row = new HashMap<>();
        row.put("department", deptName);
        row.put("visitCount", visitCount);
        row.put("prescriptionAmount", prescriptionAmount);
        row.put("traumaAmount", traumaAmount);
        return row;
    }

    // ==================== Excel 导出数据构建 ====================

    @Override
    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> buildWorkloadExcelList(Map<String, Object> stats) {
        List<Map<String, Object>> rows = (List<Map<String, Object>>) stats.get("rows");
        List<Map<String, Object>> excelList = new ArrayList<>();
        BigDecimal leaderAmt = (BigDecimal) stats.get("leaderMedicineAmount");
        BigDecimal initStock = (BigDecimal) stats.get("initialStockAmount");
        BigDecimal purchaseAmt = (BigDecimal) stats.get("purchaseTotalAmount");
        BigDecimal finalStock = (BigDecimal) stats.get("finalStockAmount");

        for (int i = 0; i < rows.size(); i++) {
            Map<String, Object> row = rows.get(i);
            Map<String, Object> vo = new LinkedHashMap<>();
            vo.put("department", row.get("department"));
            vo.put("visitCount", row.get("visitCount"));
            vo.put("prescriptionAmount", row.get("prescriptionAmount"));
            vo.put("traumaAmount", row.get("traumaAmount"));
            if (i == 0) {
                vo.put("leaderMedicineAmount", leaderAmt);
                vo.put("initialStockAmount", initStock);
                vo.put("purchaseTotalAmount", purchaseAmt);
                vo.put("finalStockAmount", finalStock);
            }
            excelList.add(vo);
        }
        return excelList;
    }

    // ==================== 库存盘点报表 ====================

    @Override
    public Map<String, Object> getInventoryCheckReport(String month) {
        Map<String, Object> result = new HashMap<>();

        InventoryCheckTask task = inventoryTaskMapper.selectOne(
                new QueryWrapper<InventoryCheckTask>().eq("month", month));
        if (task == null) {
            result.put("status", "NOT_FOUND");
            result.put("details", Collections.emptyList());
            return result;
        }

        result.put("status", task.getStatus());

        List<InventoryCheckDetail> details = inventoryDetailMapper.selectList(
                new QueryWrapper<InventoryCheckDetail>().eq("task_id", task.getId()));

        // 批量加载药品名称
        List<Long> drugIds = details.stream().map(InventoryCheckDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        List<Map<String, Object>> rows = new ArrayList<>();
        for (InventoryCheckDetail d : details) {
            Drug drug = drugMap.get(d.getDrugId());
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("drugName", drug != null ? drug.getName() : "Unknown");
            row.put("drugSpec", drug != null ? drug.getSpec() : "");
            row.put("systemStock", d.getSystemStock());
            row.put("actualStock", d.getActualStock());
            row.put("discrepancy", d.getDiscrepancy());
            row.put("remark", d.getRemark());
            rows.add(row);
        }
        result.put("details", rows);
        return result;
    }
}
