package com.gcky.durginoutsystem.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.gcky.durginoutsystem.entity.DrugBatch;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface DrugBatchMapper extends BaseMapper<DrugBatch> {

    /** FIFO 查询有效批次并加行锁，防止并发扣减 */
    @Select("SELECT * FROM drug_batches WHERE drug_id = #{drugId} AND stock_quantity > 0 ORDER BY created_at ASC FOR UPDATE")
    List<DrugBatch> selectBatchesForUpdate(@Param("drugId") Long drugId);
}
