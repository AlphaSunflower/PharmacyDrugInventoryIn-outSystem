package com.gcky.durginoutsystem.controller;

import com.alibaba.excel.EasyExcel;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.excel.DrugStatsExcel;
import com.gcky.durginoutsystem.entity.excel.OperationStatsExcel;
import com.gcky.durginoutsystem.entity.excel.WorkloadSummaryExcel;
import com.gcky.durginoutsystem.service.StatsService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.math.BigDecimal;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RequireRole({"DOCTOR", "PHARMACIST"})
@RestController
@RequestMapping("/api/v1/stats")
public class StatsController {

    @Autowired
    private StatsService statsService;

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

    private void setExcelResponse(HttpServletResponse response, String fileName) {
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String encoded = URLEncoder.encode(fileName, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + encoded + ".xlsx");
    }
}
