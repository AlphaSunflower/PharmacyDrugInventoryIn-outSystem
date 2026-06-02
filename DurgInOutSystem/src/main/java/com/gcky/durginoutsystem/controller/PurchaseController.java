package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.entity.PurchaseDetail;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.mapper.PurchaseDetailMapper;
import com.gcky.durginoutsystem.service.DrugStockService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole({"DOCTOR", "PHARMACIST"})
@Slf4j
@RestController
@RequestMapping("/api/v1/purchases")
public class PurchaseController {

    private final PurchaseDetailMapper purchaseMapper;
    private final DrugMapper drugMapper;
    private final DrugBatchMapper drugBatchMapper;
    private final DrugStockService drugStockService;

    public PurchaseController(PurchaseDetailMapper purchaseMapper,
                              DrugMapper drugMapper,
                              DrugBatchMapper drugBatchMapper,
                              DrugStockService drugStockService) {
        this.purchaseMapper = purchaseMapper;
        this.drugMapper = drugMapper;
        this.drugBatchMapper = drugBatchMapper;
        this.drugStockService = drugStockService;
    }

    // 获取某月的购进记录
    @GetMapping
    public Result<List<Map<String, Object>>> getPurchases(@RequestParam String month, @RequestParam(required = false) String drugName) {
        LocalDate start = LocalDate.parse(month + "-01");
        LocalDate end = start.plusMonths(1).minusDays(1);
        QueryWrapper<PurchaseDetail> wrapper = new QueryWrapper<>();
        wrapper.between("purchase_date", start, end);

        if (drugName != null && !drugName.trim().isEmpty()) {
            QueryWrapper<Drug> drugQuery = new QueryWrapper<>();
            drugQuery.like("name", drugName.trim());
            List<Drug> drugs = drugMapper.selectList(drugQuery);
            
            if (drugs.isEmpty()) {
                return Result.success(Collections.emptyList());
            }
            
            List<Long> drugIds = drugs.stream().map(Drug::getId).collect(Collectors.toList());
            wrapper.in("drug_id", drugIds);
        }

        wrapper.orderByDesc("purchase_date");
        List<PurchaseDetail> list = purchaseMapper.selectList(wrapper);

        // 批量加载药品名称（消除 N+1）
        List<Long> drugIds = list.stream().map(PurchaseDetail::getDrugId).distinct().collect(Collectors.toList());
        Map<Long, Drug> drugMap = drugIds.isEmpty() ? Collections.emptyMap() :
                drugMapper.selectBatchIds(drugIds).stream().collect(Collectors.toMap(Drug::getId, d -> d));

        List<Map<String, Object>> result = list.stream().map(p -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", p.getId());
            map.put("drugId", p.getDrugId());
            map.put("quantity", p.getQuantity());
            map.put("unit", p.getUnit());
            map.put("price", p.getPrice());
            map.put("totalAmount", p.getTotalAmount());
            map.put("purchaseDate", p.getPurchaseDate());
            Drug drug = drugMap.get(p.getDrugId());
            map.put("drugName", drug != null ? drug.getName() : "Unknown");
            // 从关联批次获取生产厂家
            if (p.getBatchId() != null) {
                DrugBatch batch = drugBatchMapper.selectById(p.getBatchId());
                map.put("manufacturer", batch != null ? batch.getManufacturer() : null);
            } else {
                map.put("manufacturer", null);
            }
            return map;
        }).collect(Collectors.toList());
        
        return Result.success(result);
    }

    // 批量购进 (支持按日合并)
    @Log("批量购进药品")
    @PostMapping("/batch")
    @Transactional(rollbackFor = Exception.class)
    public Result<String> addPurchaseBatch(@RequestBody List<PurchaseDetail> purchases) {
        for (PurchaseDetail purchase : purchases) {
            // 1. 创建新批次 (不再合并)
            DrugBatch batch = new DrugBatch();
            batch.setDrugId(purchase.getDrugId());
            batch.setPrice(purchase.getPrice());
            batch.setStockQuantity(purchase.getQuantity());
            batch.setInitialQuantity(purchase.getQuantity());
            batch.setManufacturer(purchase.getManufacturer());
            batch.setCreatedAt(LocalDateTime.now());
            // 自动生成批次号: YYYYMMDD_HH_mm_drugId
            LocalDateTime now = LocalDateTime.now();
            String batchNo = String.format("%04d%02d%02d_%02d_%02d_%d",
                    now.getYear(), now.getMonthValue(), now.getDayOfMonth(),
                    now.getHour(), now.getMinute(), purchase.getDrugId());
            batch.setBatchNo(batchNo);
            drugBatchMapper.insert(batch);

            // 2. 保存购进明细
            purchase.setBatchId(batch.getId());
            purchase.setCreatedAt(LocalDateTime.now());
            if (purchase.getTotalAmount() == null) {
                // 防止空指针
                BigDecimal price = purchase.getPrice() != null ? purchase.getPrice() : BigDecimal.ZERO;
                purchase.setTotalAmount(price.multiply(new BigDecimal(purchase.getQuantity())));
            }
            purchaseMapper.insert(purchase);

            // 3. 更新药品总库存和最新进价
            Drug drug = drugMapper.selectById(purchase.getDrugId());
            if (drug != null) {
                // drug.setStockQuantity(drug.getStockQuantity() + purchase.getQuantity()); // 旧逻辑：累加
                drug.setPrice(purchase.getPrice()); // 更新参考单价
                drug.setUpdatedAt(LocalDateTime.now());
                drugMapper.updateById(drug);
                
                // 新逻辑：重新计算所有批次总和 (确保一致性)
                drugStockService.updateDrugTotalStock(drug.getId());
            }
        }
        return Result.success("购进登记成功，库存已更新");
    }

}
