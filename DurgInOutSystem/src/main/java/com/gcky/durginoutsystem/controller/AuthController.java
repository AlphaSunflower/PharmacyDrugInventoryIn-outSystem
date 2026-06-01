package com.gcky.durginoutsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.gcky.durginoutsystem.common.Result;
import com.gcky.durginoutsystem.entity.User;
import com.gcky.durginoutsystem.mapper.UserMapper;
import com.gcky.durginoutsystem.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

import com.gcky.durginoutsystem.annotation.Log;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private JwtUtil jwtUtil;

    @Log("用户登录")
    @PostMapping("/login")
    public Result<Map<String, Object>> login(@RequestBody Map<String, Object> loginData) {
        String username = (String) loginData.get("username");
        String password = (String) loginData.get("password");
        String machineId = (String) loginData.get("machineId");
        Boolean autoLogin = (Boolean) loginData.get("autoLogin");

        // 简单明文密码校验，实际应加密
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("username", username);
        User user = userMapper.selectOne(queryWrapper);

        if (user == null || !user.getPassword().equals(password)) {
            return Result.error(401, "用户名或密码错误");
        }

        if (user.getStatus() == 0) {
            return Result.error(403, "账号已被停用");
        }
        
        // 处理自动登录逻辑：更新机器码
        if (Boolean.TRUE.equals(autoLogin) && machineId != null && !machineId.isEmpty()) {
            user.setMachineId(machineId);
            userMapper.updateById(user);
        }

        String token = jwtUtil.generateToken(user.getUsername(), user.getRole(), user.getId());

        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("user", user);

        return Result.success(data);
    }
    
    @Log("自动登录")
    @PostMapping("/auto-login")
    public Result<Map<String, Object>> autoLogin(@RequestBody Map<String, String> body) {
        String machineId = body.get("machineId");
        if (machineId == null || machineId.isEmpty()) {
            return Result.error(400, "机器码不能为空");
        }
        
        QueryWrapper<User> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("machine_id", machineId);
        User user = userMapper.selectOne(queryWrapper);
        
        if (user == null) {
            return Result.error(401, "未找到绑定该设备的账号，请重新登录");
        }
        
        if (user.getStatus() == 0) {
            return Result.error(403, "账号已被停用");
        }
        
        String token = jwtUtil.generateToken(user.getUsername(), user.getRole(), user.getId());
        
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("user", user);
        
        return Result.success(data);
    }
    
    @Log("用户退出")
    @PostMapping("/logout")
    public Result<String> logout(jakarta.servlet.http.HttpServletRequest request,
                                 @RequestBody(required = false) Map<String, String> body) {
        Long userId = (Long) request.getAttribute("userId");

        if (body != null && body.containsKey("machineId") && userId != null) {
            String machineId = body.get("machineId");

            User user = userMapper.selectById(userId);
            if (user != null && user.getMachineId() != null && user.getMachineId().equals(machineId)) {
                com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper<User> updateWrapper = new com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper<>();
                updateWrapper.eq("id", userId).set("machine_id", null);
                userMapper.update(null, updateWrapper);
                return Result.success("退出成功，下次需手动登录");
            }
        }
        return Result.success("退出成功");
    }
}
