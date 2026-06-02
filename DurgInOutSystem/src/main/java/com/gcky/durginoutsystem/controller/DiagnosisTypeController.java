package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.DiagnosisType;
import com.gcky.durginoutsystem.entity.PatientVisit;
import com.gcky.durginoutsystem.mapper.DiagnosisTypeMapper;
import com.gcky.durginoutsystem.mapper.PatientVisitMapper;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/diagnosis-types")
public class DiagnosisTypeController {

    private final DiagnosisTypeMapper diagnosisTypeMapper;
    private final PatientVisitMapper patientVisitMapper;

    public DiagnosisTypeController(DiagnosisTypeMapper diagnosisTypeMapper,
                                   PatientVisitMapper patientVisitMapper) {
        this.diagnosisTypeMapper = diagnosisTypeMapper;
        this.patientVisitMapper = patientVisitMapper;
    }

    // 获取诊断类型（分页）
    @RequireRole({"DOCTOR", "PHARMACIST"})
    @GetMapping
    public Result<Page<DiagnosisType>> getAll(@RequestParam(defaultValue = "1") Integer page,
                                              @RequestParam(defaultValue = "50") Integer size) {
        return Result.success(diagnosisTypeMapper.selectPage(new Page<>(page, size), null));
    }

    // 新增诊断类型
    @Log("新增诊断类型")
    @RequireRole("DOCTOR")
    @PostMapping
    @Transactional(rollbackFor = Exception.class)
    public Result<String> add(@RequestBody DiagnosisType diagnosisType) {
        if (diagnosisType.getName() == null || diagnosisType.getName().isBlank()) {
            return Result.error(400, "诊断类型名称不能为空");
        }
        // 查重
        QueryWrapper<DiagnosisType> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("name", diagnosisType.getName());
        if (diagnosisTypeMapper.selectCount(queryWrapper) > 0) {
            return Result.error(400, "该诊断类型已存在");
        }
        diagnosisTypeMapper.insert(diagnosisType);
        return Result.success("诊断类型添加成功");
    }

    // 删除诊断类型
    @Log("删除诊断类型")
    @RequireRole("DOCTOR")
    @DeleteMapping("/{id}")
    @Transactional(rollbackFor = Exception.class)
    public Result<String> delete(@PathVariable Long id) {
        // 检查是否已被使用 (patient_visits 表)
        QueryWrapper<PatientVisit> checkQuery = new QueryWrapper<>();
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
    @RequireRole("DOCTOR")
    @PutMapping("/{id}")
    @Transactional(rollbackFor = Exception.class)
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
