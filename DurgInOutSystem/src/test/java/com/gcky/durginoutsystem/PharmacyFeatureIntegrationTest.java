package com.gcky.durginoutsystem;

import com.gcky.durginoutsystem.controller.DrugController;
import com.gcky.durginoutsystem.entity.DiagnosisType;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.entity.InventoryCheckDetail;
import com.gcky.durginoutsystem.entity.InventoryCheckTask;
import com.gcky.durginoutsystem.entity.PatientVisit;
import com.gcky.durginoutsystem.entity.PurchaseDetail;
import com.gcky.durginoutsystem.entity.VisitDrug;
import com.gcky.durginoutsystem.exception.BusinessException;
import com.gcky.durginoutsystem.mapper.DiagnosisTypeMapper;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckDetailMapper;
import com.gcky.durginoutsystem.mapper.InventoryCheckTaskMapper;
import com.gcky.durginoutsystem.mapper.PatientVisitMapper;
import com.gcky.durginoutsystem.mapper.PurchaseDetailMapper;
import com.gcky.durginoutsystem.mapper.VisitDrugMapper;
import com.gcky.durginoutsystem.service.DrugStockService;
import com.gcky.durginoutsystem.service.InventoryService;
import com.gcky.durginoutsystem.service.PendingInventorySnapshotService;
import com.gcky.durginoutsystem.service.StatsService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class PharmacyFeatureIntegrationTest {

    @Autowired private DrugMapper drugMapper;
    @Autowired private DrugBatchMapper drugBatchMapper;
    @Autowired private PurchaseDetailMapper purchaseDetailMapper;
    @Autowired private InventoryCheckTaskMapper taskMapper;
    @Autowired private InventoryCheckDetailMapper detailMapper;
    @Autowired private DiagnosisTypeMapper diagnosisTypeMapper;
    @Autowired private PatientVisitMapper visitMapper;
    @Autowired private VisitDrugMapper visitDrugMapper;
    @Autowired private DrugController drugController;
    @Autowired private DrugStockService drugStockService;
    @Autowired private InventoryService inventoryService;
    @Autowired private PendingInventorySnapshotService snapshotService;
    @Autowired private StatsService statsService;

    @Test
    void pendingSnapshotSyncsOnlyTargetMonthAndLogsStockChanges() {
        LocalDate businessDate = LocalDate.of(2099, 1, 15);
        Drug drug = insertDrug("测试药品A", new BigDecimal("10.00"), 5);
        insertBatch(drug.getId(), new BigDecimal("10.00"), 5);

        InventoryCheckTask pendingTask = insertTask("2099-01", "PENDING");
        InventoryCheckDetail detail = insertDetail(pendingTask.getId(), drug.getId(), 10, null);

        snapshotService.syncDrugStock(drug.getId(), businessDate);
        detail = detailMapper.selectById(detail.getId());
        assertEquals(5, detail.getSystemStock());
        assertNull(detail.getLogContent());

        inventoryService.updateDetail(detail.getId(), 8, "", true);
        DrugBatch batch = drugBatchMapper.selectList(null).stream()
                .filter(item -> item.getDrugId().equals(drug.getId()))
                .findFirst().orElseThrow();
        batch.setStockQuantity(4);
        drugBatchMapper.updateById(batch);
        drugStockService.updateDrugTotalStock(drug.getId(), businessDate);

        detail = detailMapper.selectById(detail.getId());
        assertEquals(4, detail.getSystemStock());
        assertEquals(8, detail.getActualStock());
        assertEquals(3, detail.getDiscrepancy());
        assertEquals(PendingInventorySnapshotService.STOCK_CHANGED_LOG, detail.getLogContent());

        inventoryService.updateDetail(detail.getId(), 8, "", true);
        detail = detailMapper.selectById(detail.getId());
        assertNull(detail.getLogContent());

        InventoryCheckTask completedTask = insertTask("2099-02", "COMPLETED");
        InventoryCheckDetail completedDetail = insertDetail(completedTask.getId(), drug.getId(), 99, 99);
        snapshotService.syncDrugStock(drug.getId(), LocalDate.of(2099, 2, 10));
        completedDetail = detailMapper.selectById(completedDetail.getId());
        assertEquals(99, completedDetail.getSystemStock());
    }

    @Test
    void completeTaskIsBlockedUntilStockChangeLogIsCleared() {
        LocalDate businessDate = LocalDate.of(2099, 3, 10);
        Drug drug = insertDrug("测试药品B", new BigDecimal("8.00"), 5);
        insertBatch(drug.getId(), new BigDecimal("8.00"), 5);

        InventoryCheckTask task = insertTask("2099-03", "PENDING");
        InventoryCheckDetail detail = insertDetail(task.getId(), drug.getId(), 5, 5);
        detail.setDiscrepancy(0);
        detail.setLogContent(PendingInventorySnapshotService.STOCK_CHANGED_LOG);
        detailMapper.updateById(detail);

        BusinessException exception = assertThrows(
                BusinessException.class, () -> inventoryService.completeTask(task.getId()));
        assertTrue(exception.getMessage().contains("请重新核实库存数量"));

        inventoryService.updateDetail(detail.getId(), 5, "", true);
        inventoryService.completeTask(task.getId());
        assertEquals("COMPLETED", taskMapper.selectById(task.getId()).getStatus());
        assertNotNull(taskMapper.selectById(task.getId()).getCompletedAt());
    }

    @Test
    void batchPriceUpdateSyncsLinkedPurchaseRecords() {
        Drug drug = insertDrug("测试药品C", new BigDecimal("20.00"), 3);
        DrugBatch batch = insertBatch(drug.getId(), new BigDecimal("10.00"), 3);
        PurchaseDetail first = insertPurchase(drug.getId(), batch.getId(), 2, new BigDecimal("10.00"));
        PurchaseDetail second = insertPurchase(drug.getId(), batch.getId(), 1, new BigDecimal("10.00"));

        drugController.updateBatch(batch.getId(), Map.of("price", new BigDecimal("12.50")));

        assertEquals(new BigDecimal("12.50"), drugBatchMapper.selectById(batch.getId()).getPrice());
        assertEquals(new BigDecimal("25.00"), purchaseDetailMapper.selectById(first.getId()).getTotalAmount());
        assertEquals(new BigDecimal("12.50"), purchaseDetailMapper.selectById(second.getId()).getPrice());
        assertThrows(BusinessException.class,
                () -> drugController.updateBatch(batch.getId(), Map.of("price", new BigDecimal("-1"))));
    }

    @Test
    void drugPriceFollowsFifoStockAndIgnoresManualOverride() {
        Drug drug = insertDrug("测试药品D", new BigDecimal("99.00"), 10);
        DrugBatch oldBatch = insertBatch(drug.getId(), new BigDecimal("3.33"), 5);
        DrugBatch newBatch = insertBatch(drug.getId(), new BigDecimal("1.00"), 5);

        drugStockService.updateDrugTotalStock(drug.getId(), LocalDate.of(2099, 5, 10));
        assertEquals(0, drugMapper.selectById(drug.getId()).getPrice()
                .compareTo(new BigDecimal("3.33")));

        oldBatch.setStockQuantity(0);
        drugBatchMapper.updateById(oldBatch);
        drugStockService.updateDrugTotalStock(drug.getId(), LocalDate.of(2099, 5, 11));
        assertEquals(0, drugMapper.selectById(drug.getId()).getPrice()
                .compareTo(new BigDecimal("1.00")));

        Drug manualUpdate = new Drug();
        manualUpdate.setId(drug.getId());
        manualUpdate.setName(drug.getName());
        manualUpdate.setSpec(drug.getSpec());
        manualUpdate.setUnit(drug.getUnit());
        manualUpdate.setPrice(new BigDecimal("88.00"));
        drugController.updateDrug(drug.getId(), manualUpdate);
        assertEquals(0, drugMapper.selectById(drug.getId()).getPrice()
                .compareTo(new BigDecimal("1.00")));

        newBatch.setStockQuantity(0);
        drugBatchMapper.updateById(newBatch);
        drugStockService.updateDrugTotalStock(drug.getId(), LocalDate.of(2099, 5, 12));
        assertEquals(0, drugMapper.selectById(drug.getId()).getPrice()
                .compareTo(new BigDecimal("1.00")));
    }

    @Test
    void preparedMedicineAmountAndQuantityAreSplitByDepartment() {
        Drug drug = insertDrug("备药测试药品", new BigDecimal("10.00"), 20);
        DiagnosisType prepared = insertDiagnosis("备药调理");
        DiagnosisType normal = insertDiagnosis("普通诊断");

        PatientVisit factoryVisit = insertVisit("本厂", prepared.getId(), "2099-04-05");
        PatientVisit outsourcedVisit = insertVisit("外包", prepared.getId(), "2099-04-06");
        PatientVisit customVisit = insertVisit("本厂", normal.getId(), "2099-04-07");
        customVisit.setCustomDiagnosis("备药");
        visitMapper.updateById(customVisit);

        insertVisitDrug(factoryVisit.getId(), drug.getId(), 2, new BigDecimal("20.00"));
        insertVisitDrug(outsourcedVisit.getId(), drug.getId(), 3, new BigDecimal("30.00"));
        insertVisitDrug(customVisit.getId(), drug.getId(), 4, new BigDecimal("40.00"));

        Map<String, Object> result = statsService.calculateMonthlySummary("2099-04");
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> rows = (List<Map<String, Object>>) result.get("rows");

        Map<String, Object> factoryRow = rows.stream()
                .filter(row -> "本厂".equals(row.get("department"))).findFirst().orElseThrow();
        Map<String, Object> outsourcedRow = rows.stream()
                .filter(row -> "外包".equals(row.get("department"))).findFirst().orElseThrow();

        assertEquals(0, ((BigDecimal) factoryRow.get("preparedMedicineAmount"))
                .compareTo(new BigDecimal("20.00")));
        assertEquals(2, factoryRow.get("preparedMedicineQuantity"));
        assertEquals(0, ((BigDecimal) outsourcedRow.get("preparedMedicineAmount"))
                .compareTo(new BigDecimal("30.00")));
        assertEquals(3, outsourcedRow.get("preparedMedicineQuantity"));

        Map<String, Object> yearlyResult = statsService.calculateYearlySummary("2099");
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> yearlyRows = (List<Map<String, Object>>) yearlyResult.get("rows");
        Map<String, Object> yearlyFactoryRow = yearlyRows.stream()
                .filter(row -> "本厂".equals(row.get("department"))).findFirst().orElseThrow();
        assertEquals(2, yearlyFactoryRow.get("preparedMedicineQuantity"));
    }

    private Drug insertDrug(String name, BigDecimal price, int stock) {
        Drug drug = new Drug();
        drug.setName(name);
        drug.setSpec("10mg");
        drug.setUnit("盒");
        drug.setPrice(price);
        drug.setStockQuantity(stock);
        drug.setIsDeleted(0);
        drug.setCreatedAt(LocalDateTime.now());
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.insert(drug);
        return drug;
    }

    private DrugBatch insertBatch(Long drugId, BigDecimal price, int stock) {
        DrugBatch batch = new DrugBatch();
        batch.setDrugId(drugId);
        batch.setBatchNo("TEST-" + drugId + "-" + stock);
        batch.setPrice(price);
        batch.setStockQuantity(stock);
        batch.setInitialQuantity(stock);
        batch.setCreatedAt(LocalDateTime.now());
        drugBatchMapper.insert(batch);
        return batch;
    }

    private PurchaseDetail insertPurchase(Long drugId, Long batchId, int quantity, BigDecimal price) {
        PurchaseDetail purchase = new PurchaseDetail();
        purchase.setDrugId(drugId);
        purchase.setBatchId(batchId);
        purchase.setQuantity(quantity);
        purchase.setUnit("盒");
        purchase.setPrice(price);
        purchase.setTotalAmount(price.multiply(BigDecimal.valueOf(quantity)));
        purchase.setPurchaseDate(LocalDate.of(2099, 1, 1));
        purchase.setCreatedAt(LocalDateTime.now());
        purchaseDetailMapper.insert(purchase);
        return purchase;
    }

    private InventoryCheckTask insertTask(String month, String status) {
        InventoryCheckTask task = new InventoryCheckTask();
        task.setMonth(month);
        task.setStatus(status);
        task.setCreatedAt(LocalDateTime.now());
        taskMapper.insert(task);
        return task;
    }

    private InventoryCheckDetail insertDetail(Long taskId, Long drugId, int systemStock, Integer actualStock) {
        InventoryCheckDetail detail = new InventoryCheckDetail();
        detail.setTaskId(taskId);
        detail.setDrugId(drugId);
        detail.setSystemStock(systemStock);
        detail.setActualStock(actualStock);
        detailMapper.insert(detail);
        return detail;
    }

    private DiagnosisType insertDiagnosis(String name) {
        DiagnosisType diagnosisType = new DiagnosisType();
        diagnosisType.setName(name);
        diagnosisTypeMapper.insert(diagnosisType);
        return diagnosisType;
    }

    private PatientVisit insertVisit(String department, Long diagnosisId, String date) {
        PatientVisit visit = new PatientVisit();
        visit.setPatientName("测试患者");
        visit.setGender("男");
        visit.setAge(30);
        visit.setDiagnosisId(diagnosisId);
        visit.setDepartment(department);
        visit.setVisitDate(LocalDate.parse(date));
        visit.setStatus("COMPLETED");
        visit.setCreatedAt(LocalDateTime.now());
        visit.setUpdatedAt(LocalDateTime.now());
        visitMapper.insert(visit);
        return visit;
    }

    private VisitDrug insertVisitDrug(Long visitId, Long drugId, int quantity, BigDecimal amount) {
        VisitDrug visitDrug = new VisitDrug();
        visitDrug.setVisitId(visitId);
        visitDrug.setDrugId(drugId);
        visitDrug.setQuantity(quantity);
        visitDrug.setAmount(amount);
        visitDrug.setPrice(amount.divide(BigDecimal.valueOf(quantity)));
        visitDrugMapper.insert(visitDrug);
        return visitDrug;
    }
}
