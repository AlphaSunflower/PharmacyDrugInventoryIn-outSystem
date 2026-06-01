package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("inventory_check_tasks")
public class InventoryCheckTask {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String month; // YYYY-MM
    private String status; // PENDING, COMPLETED
    private LocalDateTime createdAt;
    private LocalDateTime completedAt;
}
