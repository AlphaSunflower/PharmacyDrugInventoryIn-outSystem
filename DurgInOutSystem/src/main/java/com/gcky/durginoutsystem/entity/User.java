package com.gcky.durginoutsystem.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("users")
public class User {
    @TableId(type = IdType.AUTO)
    private Long id;
    @NotBlank(message = "用户名不能为空")
    private String username;
    @JsonIgnore
    private String password;
    private String realName;
    private String role; // ADMIN, DOCTOR, PHARMACIST
    private Integer status; // 1: enable, 0: disable
    private String machineId; // 绑定的机器码
    private LocalDateTime createdAt;
}
