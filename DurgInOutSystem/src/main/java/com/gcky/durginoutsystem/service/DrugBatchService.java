package com.gcky.durginoutsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.gcky.durginoutsystem.entity.DrugBatch;

public interface DrugBatchService extends IService<DrugBatch> {
    /**
     * Migrate existing drug stock to initial batches
     */
    void migrateData();
}
