package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.Drug;
import com.gcky.durginoutsystem.mapper.DrugMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole({"DOCTOR", "PHARMACIST"})
@RestController
@RequestMapping("/api/v1/drugs")
public class DrugController {

    @Autowired
    private DrugMapper drugMapper;

    @Autowired
    private com.gcky.durginoutsystem.service.DrugBatchService drugBatchService;
    @Autowired
    private com.gcky.durginoutsystem.mapper.DrugBatchMapper drugBatchMapper;

    @Log("执行数据迁移")
    @PostMapping("/migrate-batches")
    public Result<String> migrateBatches() {
        drugBatchService.migrateData();
        return Result.success("数据迁移成功");
    }

    // 查询药品列表
    @GetMapping
    public Result<Page<Drug>> getDrugs(@RequestParam(defaultValue = "1") Integer page,
                                       @RequestParam(defaultValue = "10") Integer size,
                                       @RequestParam(required = false) String keyword,
                                       @RequestParam(required = false) Integer minStock,
                                       @RequestParam(required = false) Integer maxStock) {
        Page<Drug> drugPage = new Page<>(page, size);
        QueryWrapper<Drug> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("is_deleted", 0);
        if (keyword != null && !keyword.isEmpty()) {
            queryWrapper.like("name", keyword);
        }
        if (minStock != null) {
            queryWrapper.ge("stock_quantity", minStock);
        }
        if (maxStock != null) {
            queryWrapper.le("stock_quantity", maxStock);
        }
        queryWrapper.orderByDesc("created_at");
        Page<Drug> result = drugMapper.selectPage(drugPage, queryWrapper);

        // 填充批次信息
        for (Drug drug : result.getRecords()) {
            QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> batchQuery = new QueryWrapper<>();
            batchQuery.eq("drug_id", drug.getId())
                      .ge("stock_quantity", 0)
                      .orderByAsc("created_at");
            drug.setBatchList(drugBatchMapper.selectList(batchQuery));
        }

        return Result.success(result);
    }

    // 新增药品
    @Log("新增药品")
    @PostMapping
    public Result<String> addDrug(@RequestBody Drug drug) {
        drug.setIsDeleted(0);
        drug.setStockQuantity(0); // 初始库存为0，需通过购进增加
        drug.setCreatedAt(LocalDateTime.now());
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.insert(drug);

        // 自动生成初始化批次
        com.gcky.durginoutsystem.entity.DrugBatch batch = new com.gcky.durginoutsystem.entity.DrugBatch();
        batch.setDrugId(drug.getId());
        batch.setBatchNo("INIT"); // 初始化批次号
        batch.setPrice(drug.getPrice());
        batch.setStockQuantity(0);
        batch.setInitialQuantity(0);
        batch.setCreatedAt(LocalDateTime.now());
        drugBatchMapper.insert(batch);

        return Result.success("药品添加成功");
    }

    // 修改批次库存
    @Autowired
    private com.gcky.durginoutsystem.service.DrugStockService drugStockService;

    @Log("修改批次库存")
    @PutMapping("/batch/{batchId}/stock")
    public Result<String> updateBatchStock(@PathVariable Long batchId, @RequestParam Integer quantity) {
        com.gcky.durginoutsystem.entity.DrugBatch batch = drugBatchMapper.selectById(batchId);
        if (batch == null) {
            return Result.error(404, "批次不存在");
        }

        batch.setStockQuantity(quantity);
        drugBatchMapper.updateById(batch);

        // 同步更新总库存
        drugStockService.updateDrugTotalStock(batch.getDrugId());

        return Result.success("库存更新成功");
    }

    // 修改药品
    @Log("修改药品信息")
    @PutMapping("/{id}")
    public Result<String> updateDrug(@PathVariable Long id, @RequestBody Drug drug) {
        drug.setId(id);
        
        // 如果修改了库存数量，且当前没有批次信息，则自动生成初始化批次
        if (drug.getStockQuantity() != null) {
            QueryWrapper<com.gcky.durginoutsystem.entity.DrugBatch> batchQuery = new QueryWrapper<>();
            batchQuery.eq("drug_id", id);
            Long batchCount = drugBatchMapper.selectCount(batchQuery);
            
            if (batchCount == 0) {
                // 获取当前药品信息以获取价格（如果前端没传）
                Drug currentDrug = drugMapper.selectById(id);
                java.math.BigDecimal price = drug.getPrice() != null ? drug.getPrice() : (currentDrug != null ? currentDrug.getPrice() : java.math.BigDecimal.ZERO);
                
                com.gcky.durginoutsystem.entity.DrugBatch batch = new com.gcky.durginoutsystem.entity.DrugBatch();
                batch.setDrugId(id);
                batch.setBatchNo("INIT_AUTO"); // 自动生成的初始化批次
                batch.setPrice(price);
                batch.setStockQuantity(drug.getStockQuantity());
                batch.setInitialQuantity(drug.getStockQuantity());
                batch.setCreatedAt(LocalDateTime.now());
                drugBatchMapper.insert(batch);
            }
        }
        
        drug.setUpdatedAt(LocalDateTime.now());
        drugMapper.updateById(drug);
        return Result.success("药品信息更新成功");
    }

    @Autowired
    private com.gcky.durginoutsystem.mapper.VisitDrugMapper visitDrugMapper;

    // 删除药品 (软删除)
    @Log("删除药品")
    @DeleteMapping("/{id}")
    public Result<String> deleteDrug(@PathVariable Long id) {
        // 检查该药品是否有相关的使用记录 (visit_drugs)
        QueryWrapper<com.gcky.durginoutsystem.entity.VisitDrug> checkQuery = new QueryWrapper<>();
        checkQuery.eq("drug_id", id);
        Long count = visitDrugMapper.selectCount(checkQuery);
        
        if (count > 0) {
            return Result.error(400, "该药品已被使用过，无法删除！");
        }

        Drug drug = new Drug();
        drug.setId(id);
        drug.setIsDeleted(1);
        drugMapper.updateById(drug);
        return Result.success("药品已删除");
    }
}
