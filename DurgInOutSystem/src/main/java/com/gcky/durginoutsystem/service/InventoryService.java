package com.gcky.durginoutsystem.service;

import com.gcky.durginoutsystem.entity.InventoryCheckDetail;
import com.gcky.durginoutsystem.entity.InventoryCheckTask;

import java.util.List;
import java.util.Map;

public interface InventoryService {
    Long generateTask(String month);
    List<Map<String, Object>> getTaskDetails(Long taskId);
    void updateDetail(Long detailId, Integer actualStock, String remark);
    void completeTask(Long taskId);
    
    void reopenTask(Long taskId);

    void deleteTask(Long taskId);

    List<InventoryCheckTask> getPendingTasks();
}
