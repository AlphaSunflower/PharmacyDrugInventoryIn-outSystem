package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.DiagnosisType;
import com.gcky.durginoutsystem.mapper.DiagnosisTypeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import com.gcky.durginoutsystem.annotation.Log;

@RestController
@RequestMapping("/api/v1/diagnosis-types")
@CrossOrigin
public class DiagnosisTypeController {

    @Autowired
    private DiagnosisTypeMapper diagnosisTypeMapper;

    // 获取所有诊断类型
    @GetMapping
    public Result<List<DiagnosisType>> getAll() {
        return Result.success(diagnosisTypeMapper.selectList(null));
    }

    // 新增诊断类型
    @Log("新增诊断类型")
    @PostMapping
    public Result<String> add(@RequestBody DiagnosisType diagnosisType) {
        // 查重
        QueryWrapper<DiagnosisType> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("name", diagnosisType.getName());
        if (diagnosisTypeMapper.selectCount(queryWrapper) > 0) {
            return Result.error(400, "该诊断类型已存在");
        }
        diagnosisTypeMapper.insert(diagnosisType);
        return Result.success("诊断类型添加成功");
    }

    @Autowired
    private com.gcky.durginoutsystem.mapper.PatientVisitMapper patientVisitMapper;

    // 删除诊断类型
    @Log("删除诊断类型")
    @DeleteMapping("/{id}")
    public Result<String> delete(@PathVariable Long id) {
        // 检查是否已被使用 (patient_visits 表)
        QueryWrapper<com.gcky.durginoutsystem.entity.PatientVisit> checkQuery = new QueryWrapper<>();
        checkQuery.eq("diagnosis_id", id);
        Long count = patientVisitMapper.selectCount(checkQuery);
        
        if (count > 0) {
            return Result.error(400, "该诊断类型已被使用，无法删除！");
        }

        try {
            diagnosisTypeMapper.deleteById(id);
            return Result.success("删除成功");
        } catch (Exception e) {
            return Result.error(500, "删除失败，该类型可能已被使用");
        }
    }

    // 修改诊断类型
    @Log("修改诊断类型")
    @PutMapping("/{id}")
    public Result<String> update(@PathVariable Long id, @RequestBody DiagnosisType diagnosisType) {
        DiagnosisType existing = diagnosisTypeMapper.selectById(id);
        if (existing == null) {
            return Result.error(404, "诊断类型不存在");
        }

        // 查重 (排除自己)
        QueryWrapper<DiagnosisType> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("name", diagnosisType.getName())
                    .ne("id", id);
        if (diagnosisTypeMapper.selectCount(queryWrapper) > 0) {
            return Result.error(400, "该诊断类型名称已存在");
        }

        existing.setName(diagnosisType.getName());
        if (diagnosisType.getRemark() != null) {
            existing.setRemark(diagnosisType.getRemark());
        }
        diagnosisTypeMapper.updateById(existing);
        return Result.success("修改成功");
    }
}
