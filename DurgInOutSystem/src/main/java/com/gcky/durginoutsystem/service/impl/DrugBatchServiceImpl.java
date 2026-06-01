package com.gcky.durginoutsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.entity.DrugBatch;
import com.gcky.durginoutsystem.mapper.DrugBatchMapper;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import com.gcky.durginoutsystem.service.DrugBatchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class DrugBatchServiceImpl extends ServiceImpl<DrugBatchMapper, DrugBatch> implements DrugBatchService {

    @Autowired
    private DrugMapper drugMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void migrateData() {
        // Find all drugs with stock > 0
        QueryWrapper<Drug> query = new QueryWrapper<>();
        query.gt("stock_quantity", 0);
        List<Drug> drugs = drugMapper.selectList(query);

        for (Drug drug : drugs) {
            // Check if batch already exists for this drug to prevent double migration
            long count = this.count(new QueryWrapper<DrugBatch>().eq("drug_id", drug.getId()));
            if (count > 0) {
                continue;
            }

            DrugBatch batch = new DrugBatch();
            batch.setDrugId(drug.getId());
            batch.setBatchNo("INITIAL_BATCH");
            batch.setPrice(drug.getPrice());
            batch.setStockQuantity(drug.getStockQuantity());
            batch.setInitialQuantity(drug.getStockQuantity());
            // production/expiry unknown, leave null
            batch.setCreatedAt(LocalDateTime.now());

            this.save(batch);
        }
    }
}
