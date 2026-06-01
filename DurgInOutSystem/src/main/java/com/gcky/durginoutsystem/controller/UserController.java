package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.User;
import com.gcky.durginoutsystem.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

import com.gcky.durginoutsystem.annotation.Log;
import com.gcky.durginoutsystem.annotation.RequireRole;

@RequireRole("ADMIN")
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private UserMapper userMapper;

    // 获取用户列表 (Admin only)
    @GetMapping
    public Result<Page<User>> getUsers(@RequestParam(defaultValue = "1") Integer page,
                                       @RequestParam(defaultValue = "10") Integer size,
                                       @RequestParam(required = false) String role) {
        Page<User> userPage = new Page<>(page, size);
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        if (role != null && !role.isEmpty()) {
            queryWrapper.eq("role", role);
        }
        queryWrapper.orderByDesc("created_at");
        return Result.success(userMapper.selectPage(userPage, queryWrapper));
    }

    // 新增用户
    @Log("新增系统用户")
    @PostMapping
    public Result<String> addUser(@RequestBody User user) {
        // 检查用户名是否已存在
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", user.getUsername());
        if (userMapper.selectCount(queryWrapper) > 0) {
            return Result.error(400, "用户名已存在");
        }
        
        user.setStatus(1); // 默认启用
        user.setCreatedAt(LocalDateTime.now());
        // 实际应加密密码
        userMapper.insert(user);
        return Result.success("用户创建成功");
    }

    // 修改用户
    @Log("修改系统用户")
    @PutMapping("/{id}")
    public Result<String> updateUser(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        // 不允许修改用户名
        user.setUsername(null);
        userMapper.updateById(user);
        return Result.success("用户信息更新成功");
    }

    // 修改用户状态 (停用/启用)
    @Log("修改用户状态")
    @PatchMapping("/{id}/status")
    public Result<String> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        User user = new User();
        user.setId(id);
        user.setStatus(status);
        userMapper.updateById(user);
        return Result.success("状态更新成功");
    }
}
