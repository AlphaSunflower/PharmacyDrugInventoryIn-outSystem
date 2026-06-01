package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

@Service
public class DrugStockService {

    @Autowired
    private DrugBatchMapper drugBatchMapper;
    @Autowired
    private DrugMapper drugMapper;

    /** 根据所有批次库存之和重新计算药品总库存 */
    public void updateDrugTotalStock(Long drugId) {
        QueryWrapper<DrugBatch> query = new QueryWrapper<>();
        query.eq("drug_id", drugId);
        query.select("IFNULL(SUM(stock_quantity), 0) as total");

        Map<String, Object> result = drugBatchMapper.selectMaps(query).stream().findFirst().orElse(null);
        int totalStock = 0;
        if (result != null && result.get("total") != null) {
            totalStock = ((BigDecimal) result.get("total")).intValue();
        }

        Drug drug = new Drug();
        drug.setId(drugId);
        drug.setStockQuantity(totalStock);
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.updateById(drug);
    }
}
