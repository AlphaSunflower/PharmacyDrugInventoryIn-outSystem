package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

@Service
public class DrugStockService {

    @Autowired
    private DrugBatchMapper drugBatchMapper;
    @Autowired
    private DrugMapper drugMapper;
    @Autowired
    private PendingInventorySnapshotService pendingInventorySnapshotService;

    /** 根据所有批次库存之和重新计算药品总库存 */
    public void updateDrugTotalStock(Long drugId) {
        updateDrugTotalStock(drugId, LocalDate.now());
    }

    /** 重算总库存，并按业务日期同步对应月份的待完成盘点快照。 */
    public void updateDrugTotalStock(Long drugId, LocalDate businessDate, LocalDate... additionalBusinessDates) {
        List<DrugBatch> batches = drugBatchMapper.selectList(new QueryWrapper<DrugBatch>()
                .eq("drug_id", drugId)
                .orderByAsc("created_at")
                .orderByAsc("id"));
        int totalStock = batches.stream()
                .map(DrugBatch::getStockQuantity)
                .filter(stock -> stock != null)
                .mapToInt(Integer::intValue)
                .sum();

        Drug currentDrug = drugMapper.selectById(drugId);
        BigDecimal mappedPrice = batches.stream()
                .filter(batch -> batch.getStockQuantity() != null && batch.getStockQuantity() > 0)
                .map(DrugBatch::getPrice)
                .filter(price -> price != null)
                .findFirst()
                .orElseGet(() -> {
                    if (!batches.isEmpty()) {
                        BigDecimal latestPrice = batches.get(batches.size() - 1).getPrice();
                        if (latestPrice != null) {
                            return latestPrice;
                        }
                    }
                    return currentDrug != null && currentDrug.getPrice() != null
                            ? currentDrug.getPrice() : BigDecimal.ZERO;
                });

        Drug drug = new Drug();
        drug.setId(drugId);
        drug.setStockQuantity(totalStock);
        drug.setPrice(mappedPrice);
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.updateById(drug);

        Set<LocalDate> businessDates = new LinkedHashSet<>();
        if (businessDate != null) {
            businessDates.add(businessDate);
        }
        if (additionalBusinessDates != null) {
            for (LocalDate additionalDate : additionalBusinessDates) {
                if (additionalDate != null) {
                    businessDates.add(additionalDate);
                }
            }
        }
        if (businessDates.isEmpty()) {
            businessDates.add(LocalDate.now());
        }
        businessDates.forEach(date -> pendingInventorySnapshotService.syncDrugStock(drugId, date));
    }
}
