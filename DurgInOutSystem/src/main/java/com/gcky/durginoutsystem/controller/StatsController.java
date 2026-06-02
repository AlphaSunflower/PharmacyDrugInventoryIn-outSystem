package com.gcky.durginoutsystem.controller;

import com.alibaba.excel.EasyExcel;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.excel.DrugStatsExcel;
import com.gcky.durginoutsystem.entity.excel.OperationStatsExcel;
import com.gcky.durginoutsystem.entity.excel.InventoryCheckExcel;
import com.gcky.durginoutsystem.entity.excel.PurchasePlanExcel;
import com.gcky.durginoutsystem.entity.excel.WorkloadSummaryExcel;
import com.gcky.durginoutsystem.exception.BusinessException;
import com.gcky.durginoutsystem.service.StatsService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RequireRole({"DOCTOR", "PHARMACIST"})
@RestController
@RequestMapping("/api/v1/stats")
public class StatsController {

    @Autowired
    private StatsService statsService;

    @Autowired
    private com.gcky.durginoutsystem.mapper.PurchasePlanMapper purchasePlanMapper;
    @Autowired
    private com.gcky.durginoutsystem.mapper.PurchasePlanDetailMapper purchasePlanDetailMapper;
    @Autowired
    private com.gcky.durginoutsystem.mapper.DrugMapper drugMapper;

    // ==================== API 端点 ====================

    @GetMapping("/drugs")
    public Result<Map<String, Object>> getDrugStats(@RequestParam String month) {
        return Result.success(statsService.calculateDrugStats(month));
    }

    @GetMapping("/operations")
    public Result<Map<String, Object>> getOperationStats(@RequestParam String month) {
        return Result.success(statsService.calculateOperationStats(month));
    }

    @GetMapping("/monthly-summary")
    public Result<Map<String, Object>> getMonthlySummary(@RequestParam String month) {
        return Result.success(statsService.calculateMonthlySummary(month));
    }

    @GetMapping("/yearly-summary")
    public Result<Map<String, Object>> getYearlySummary(@RequestParam String year) {
        return Result.success(statsService.calculateYearlySummary(year));
    }

    // ==================== 采购计划报表 ====================

    @GetMapping("/purchase-plan")
    public Result<Map<String, Object>> getPurchasePlan(@RequestParam String month) {
        Map<String, Object> result = new HashMap<>();

        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<com.gcky.durginoutsystem.entity.PurchasePlan> planQuery =
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        planQuery.eq("month", month);
        com.gcky.durginoutsystem.entity.PurchasePlan plan = purchasePlanMapper.selectOne(planQuery);

        if (plan == null) {
            result.put("status", "NOT_FOUND");
            result.put("details", java.util.Collections.emptyList());
            return Result.success(result);
        }

        result.put("status", plan.getStatus());

        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<com.gcky.durginoutsystem.entity.PurchasePlanDetail> detailQuery =
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        detailQuery.eq("plan_id", plan.getId());
        List<com.gcky.durginoutsystem.entity.PurchasePlanDetail> details = purchasePlanDetailMapper.selectList(detailQuery);

        List<Long> drugIds = details.stream().map(com.gcky.durginoutsystem.entity.PurchasePlanDetail::getDrugId).distinct().collect(java.util.stream.Collectors.toList());
        Map<Long, com.gcky.durginoutsystem.entity.Drug> drugMap = drugIds.isEmpty() ? java.util.Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(java.util.stream.Collectors.toMap(com.gcky.durginoutsystem.entity.Drug::getId, d -> d));

        List<Map<String, Object>> detailList = details.stream().map(d -> {
            Map<String, Object> map = new HashMap<>();
            com.gcky.durginoutsystem.entity.Drug drug = drugMap.get(d.getDrugId());
            map.put("drugName", drug != null ? drug.getName() : "Unknown");
            map.put("spec", d.getSpec());
            map.put("unit", d.getUnit());
            map.put("purchasePrice", d.getPurchasePrice());
            map.put("manufacturer", d.getManufacturer());
            map.put("plannedQuantity", d.getPlannedQuantity());
            return map;
        }).collect(java.util.stream.Collectors.toList());

        result.put("details", detailList);
        return Result.success(result);
    }

    // ==================== 库存盘点报表 ====================

    @GetMapping("/inventory-check")
    public Result<Map<String, Object>> getInventoryCheck(@RequestParam String month) {
        return Result.success(statsService.getInventoryCheckReport(month));
    }

    @GetMapping("/inventory-check/export")
    public void exportInventoryCheck(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> report = statsService.getInventoryCheckReport(month);
        String status = (String) report.get("status");
        if (!"COMPLETED".equals(status)) {
            response.setStatus(400);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":400,\"message\":\"该月份盘点尚未完成或不存在，无法导出\"}");
            return;
        }
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> details = (List<Map<String, Object>>) report.get("details");
        List<InventoryCheckExcel> excelList = new ArrayList<>();
        for (Map<String, Object> row : details) {
            InventoryCheckExcel vo = new InventoryCheckExcel();
            vo.setDrugName((String) row.get("drugName"));
            vo.setDrugSpec((String) row.get("drugSpec"));
            vo.setSystemStock((Integer) row.get("systemStock"));
            vo.setActualStock((Integer) row.get("actualStock"));
            vo.setDiscrepancy((Integer) row.get("discrepancy"));
            vo.setRemark((String) row.get("remark"));
            excelList.add(vo);
        }
        setExcelResponse(response, "库存盘点报表_" + month);
        EasyExcel.write(response.getOutputStream(), InventoryCheckExcel.class).sheet("库存盘点").doWrite(excelList);
    }

    // ==================== Excel 导出 ====================

    @GetMapping("/drugs/export")
    public void exportDrugStats(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = statsService.calculateDrugStats(month);
        @SuppressWarnings("unchecked")
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
        @SuppressWarnings("unchecked")
        Map<String, Object> summary = (Map<String, Object>) stats.get("summary");
        DrugStatsExcel sumVo = new DrugStatsExcel();
        sumVo.setDrugName("合计");
        sumVo.setStartAmount((BigDecimal) summary.get("totalStartAmount"));
        sumVo.setPurchaseAmount((BigDecimal) summary.get("totalPurchaseAmount"));
        sumVo.setUseAmount((BigDecimal) summary.get("totalUseAmount"));
        sumVo.setEndAmount((BigDecimal) summary.get("totalEndAmount"));
        excelList.add(sumVo);

        setExcelResponse(response, "药品进销存报表_" + month);
        EasyExcel.write(response.getOutputStream(), DrugStatsExcel.class).sheet("药品进销存").doWrite(excelList);
    }

    @GetMapping("/operations/export")
    public void exportOperationStats(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = statsService.calculateOperationStats(month);
        @SuppressWarnings("unchecked")
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
        @SuppressWarnings("unchecked")
        Map<String, Object> summary = (Map<String, Object>) stats.get("summary");
        OperationStatsExcel sumVo = new OperationStatsExcel();
        sumVo.setDate("月度汇总");
        sumVo.setVisits((Integer) summary.get("totalVisits"));
        sumVo.setTotalCost((BigDecimal) summary.get("totalCost"));
        sumVo.setAvgCost((BigDecimal) summary.get("avgCost"));
        sumVo.setDiagnosisDetails("");
        excelList.add(sumVo);

        setExcelResponse(response, "运营统计报表_" + month);
        EasyExcel.write(response.getOutputStream(), OperationStatsExcel.class).sheet("运营统计").doWrite(excelList);
    }

    @GetMapping("/monthly-summary/export")
    public void exportMonthlySummary(@RequestParam String month, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = statsService.calculateMonthlySummary(month);
        List<Map<String, Object>> excelList = statsService.buildWorkloadExcelList(stats);
        List<WorkloadSummaryExcel> rows = new ArrayList<>();
        for (Map<String, Object> map : excelList) {
            WorkloadSummaryExcel vo = new WorkloadSummaryExcel();
            vo.setDepartment((String) map.get("department"));
            vo.setVisitCount((Integer) map.get("visitCount"));
            vo.setPrescriptionAmount((BigDecimal) map.get("prescriptionAmount"));
            vo.setTraumaAmount((BigDecimal) map.get("traumaAmount"));
            if (map.containsKey("leaderMedicineAmount")) {
                vo.setLeaderMedicineAmount((BigDecimal) map.get("leaderMedicineAmount"));
                vo.setInitialStockAmount((BigDecimal) map.get("initialStockAmount"));
                vo.setPurchaseTotalAmount((BigDecimal) map.get("purchaseTotalAmount"));
                vo.setFinalStockAmount((BigDecimal) map.get("finalStockAmount"));
            }
            rows.add(vo);
        }

        setExcelResponse(response, "月度汇总报表_" + month);
        EasyExcel.write(response.getOutputStream(), WorkloadSummaryExcel.class).sheet("月度汇总").doWrite(rows);
    }

    @GetMapping("/yearly-summary/export")
    public void exportYearlySummary(@RequestParam String year, HttpServletResponse response) throws IOException {
        Map<String, Object> stats = statsService.calculateYearlySummary(year);
        List<Map<String, Object>> excelList = statsService.buildWorkloadExcelList(stats);
        List<WorkloadSummaryExcel> rows = new ArrayList<>();
        for (Map<String, Object> map : excelList) {
            WorkloadSummaryExcel vo = new WorkloadSummaryExcel();
            vo.setDepartment((String) map.get("department"));
            vo.setVisitCount((Integer) map.get("visitCount"));
            vo.setPrescriptionAmount((BigDecimal) map.get("prescriptionAmount"));
            vo.setTraumaAmount((BigDecimal) map.get("traumaAmount"));
            if (map.containsKey("leaderMedicineAmount")) {
                vo.setLeaderMedicineAmount((BigDecimal) map.get("leaderMedicineAmount"));
                vo.setInitialStockAmount((BigDecimal) map.get("initialStockAmount"));
                vo.setPurchaseTotalAmount((BigDecimal) map.get("purchaseTotalAmount"));
                vo.setFinalStockAmount((BigDecimal) map.get("finalStockAmount"));
            }
            rows.add(vo);
        }

        setExcelResponse(response, "年度汇总报表_" + year);
        EasyExcel.write(response.getOutputStream(), WorkloadSummaryExcel.class).sheet("年度汇总").doWrite(rows);
    }

    // ==================== 采购计划导出 ====================

    @GetMapping("/purchase-plan/export")
    public void exportPurchasePlan(@RequestParam String month, HttpServletResponse response) throws IOException {
        // 查询当月采购计划
        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<com.gcky.durginoutsystem.entity.PurchasePlan> planQuery =
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        planQuery.eq("month", month);
        com.gcky.durginoutsystem.entity.PurchasePlan plan = purchasePlanMapper.selectOne(planQuery);

        if (plan == null) {
            response.setStatus(400);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":400,\"message\":\"未找到当月采购计划，请先生成采购计划\"}");
            return;
        }
        if (!"COMPLETED".equals(plan.getStatus())) {
            response.setStatus(400);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":400,\"message\":\"请先完成当月采购计划后再导出\"}");
            return;
        }

        // 查询明细
        com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<com.gcky.durginoutsystem.entity.PurchasePlanDetail> detailQuery =
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<>();
        detailQuery.eq("plan_id", plan.getId());
        List<com.gcky.durginoutsystem.entity.PurchasePlanDetail> details = purchasePlanDetailMapper.selectList(detailQuery);

        // 批量加载药品名称
        List<Long> drugIds = details.stream().map(com.gcky.durginoutsystem.entity.PurchasePlanDetail::getDrugId).distinct().collect(java.util.stream.Collectors.toList());
        Map<Long, com.gcky.durginoutsystem.entity.Drug> drugMap = drugIds.isEmpty() ? java.util.Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(java.util.stream.Collectors.toMap(com.gcky.durginoutsystem.entity.Drug::getId, d -> d));

        List<PurchasePlanExcel> excelList = new ArrayList<>();
        for (com.gcky.durginoutsystem.entity.PurchasePlanDetail d : details) {
            PurchasePlanExcel vo = new PurchasePlanExcel();
            com.gcky.durginoutsystem.entity.Drug drug = drugMap.get(d.getDrugId());
            vo.setDrugName(drug != null ? drug.getName() : "Unknown");
            vo.setSpec(d.getSpec());
            vo.setUnit(d.getUnit());
            vo.setPurchasePrice(d.getPurchasePrice());
            vo.setManufacturer(d.getManufacturer());
            vo.setPlannedQuantity(d.getPlannedQuantity());
            excelList.add(vo);
        }

        setExcelResponse(response, "采购计划_" + month);
        EasyExcel.write(response.getOutputStream(), PurchasePlanExcel.class).sheet("采购计划").doWrite(excelList);
    }

    private void setExcelResponse(HttpServletResponse response, String fileName) {
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String encoded = URLEncoder.encode(fileName, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + encoded + ".xlsx");
    }
}
