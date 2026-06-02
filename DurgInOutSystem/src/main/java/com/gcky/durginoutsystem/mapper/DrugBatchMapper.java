package com.gcky.durginoutsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.gcky.durginoutsystem.entity.DrugBatch;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface DrugBatchMapper extends BaseMapper<DrugBatch> {

    /** FIFO 查询有效批次并加行锁，防止并发扣减 */
    @Select("SELECT * FROM drug_batches WHERE drug_id = #{drugId} AND stock_quantity > 0 ORDER BY created_at ASC FOR UPDATE")
    List<DrugBatch> selectBatchesForUpdate(@Param("drugId") Long drugId);

    /** 原子性增加指定批次的库存（DB 侧运算，无竞态） */
    @Update("UPDATE drug_batches SET stock_quantity = stock_quantity + #{quantity} WHERE id = #{batchId}")
    int incrementStock(@Param("batchId") Long batchId, @Param("quantity") int quantity);

    /** 查询最新批次并加行锁（用于盘盈场景的先锁再写） */
    @Select("SELECT * FROM drug_batches WHERE drug_id = #{drugId} ORDER BY created_at DESC LIMIT 1 FOR UPDATE")
    DrugBatch selectLatestForUpdate(@Param("drugId") Long drugId);

    /** 获取某药品最新批次（用于取进货价和生产厂家） */
    @Select("SELECT * FROM drug_batches WHERE drug_id = #{drugId} ORDER BY created_at DESC LIMIT 1")
    DrugBatch selectLatestByDrugId(@Param("drugId") Long drugId);

    /** 获取某药品所有批次（按入库时间倒序，用于厂家历史列表） */
    @Select("SELECT * FROM drug_batches WHERE drug_id = #{drugId} ORDER BY created_at DESC")
    List<DrugBatch> selectAllByDrugIdOrderByCreatedAtDesc(@Param("drugId") Long drugId);
}
