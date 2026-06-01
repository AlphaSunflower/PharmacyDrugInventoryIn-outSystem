# 药品出入库系统 API 接口设计方案

## 1. 设计规范

### 1.1 基础规范
- **架构风格**: RESTful API
- **数据格式**: JSON (Content-Type: application/json)
- **字符编码**: UTF-8
- **接口版本**: URL 前缀 `/api/v1`
- **时间格式**: ISO 8601 (`yyyy-MM-dd HH:mm:ss`)

### 1.2 状态码规范 (HTTP Status Code)
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或Token失效
- `403 Forbidden`: 无权限访问
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

### 1.3 统一响应结构
```json
{
  "code": 200,          // 业务状态码 (200成功, 其他为错误码)
  "message": "success", // 提示信息
  "data": { ... }       // 业务数据
}
```

### 1.4 权限控制 (RBAC)
- 基于 JWT (JSON Web Token) 进行认证。
- 请求头携带: `Authorization: Bearer <token>`
- 角色定义:
  - `ADMIN`: 管理员
  - `DOCTOR`: 医师
  - `PHARMACIST`: 药师

---

## 2. 核心接口定义

### 2.1 用户认证 (Auth)

#### 2.1.1 用户登录
- **方法**: `POST`
- **路径**: `/auth/login`
- **描述**: 用户凭账号密码获取 Token。
- **请求体**:
  ```json
  {
    "username": "admin",
    "password": "encrypted_password"
  }
  ```
- **响应**:
  ```json
  {
    "token": "eyJhbGciOiJIUzI1...",
    "user": { "id": 1, "username": "admin", "role": "ADMIN", "realName": "管理员" }
  }
  ```

#### 2.1.2 退出登录
- **方法**: `POST`
- **路径**: `/auth/logout`

---

### 2.2 用户管理 (User - Admin Only)

#### 2.2.1 获取用户列表
- **方法**: `GET`
- **路径**: `/users`
- **参数**: `page` (页码), `size` (每页条数), `role` (筛选角色)
- **权限**: `ADMIN`

#### 2.2.2 新增用户
- **方法**: `POST`
- **路径**: `/users`
- **请求体**:
  ```json
  {
    "username": "doctor1",
    "password": "default_password",
    "realName": "张医生",
    "role": "DOCTOR"
  }
  ```
- **权限**: `ADMIN`

#### 2.2.3 修改用户信息/重置密码
- **方法**: `PUT`
- **路径**: `/users/{id}`
- **权限**: `ADMIN`

#### 2.2.4 停用/启用用户
- **方法**: `PATCH`
- **路径**: `/users/{id}/status`
- **参数**: `status` (0:停用, 1:启用)
- **权限**: `ADMIN`

---

### 2.3 药品管理 (Drug)

#### 2.3.1 查询药品列表
- **方法**: `GET`
- **路径**: `/drugs`
- **参数**: `keyword` (名称/拼音简拼), `page`, `size`
- **权限**: `DOCTOR`, `PHARMACIST`
- **响应**: 包含库存信息。

#### 2.3.2 新增药品
- **方法**: `POST`
- **路径**: `/drugs`
- **请求体**:
  ```json
  {
    "name": "阿莫西林",
    "spec": "0.25g*24粒",
    "unit": "盒",
    "price": 15.50
  }
  ```
- **权限**: `DOCTOR`, `PHARMACIST`

#### 2.3.3 修改药品
- **方法**: `PUT`
- **路径**: `/drugs/{id}`
- **权限**: `DOCTOR`, `PHARMACIST`

#### 2.3.4 药品购进登记 (入库)
- **方法**: `POST`
- **路径**: `/purchases`
- **描述**: 记录购进明细并增加库存。
- **请求体**:
  ```json
  {
    "drugId": 101,
    "quantity": 100,
    "unit": "盒",
    "price": 14.00, // 进价
    "purchaseDate": "2023-10-25"
  }
  ```
- **权限**: `PHARMACIST`, `DOCTOR` (根据需求文档描述，医师和药师都可以对药品进行增删改查，但通常购进由药师或管理员负责，此处开放给两者或按需限制)

---

### 2.4 诊断类型管理 (Diagnosis)

#### 2.4.1 获取诊断类型列表
- **方法**: `GET`
- **路径**: `/diagnosis-types`
- **权限**: `DOCTOR`, `PHARMACIST`

#### 2.4.2 新增诊断类型
- **方法**: `POST`
- **路径**: `/diagnosis-types`
- **请求体**: `{ "name": "流感", "remark": "季节性" }`
- **权限**: `DOCTOR`

---

### 2.5 患者就诊与发药 (Visit & Dispense)

#### 2.5.1 提交就诊记录 (开方)
- **方法**: `POST`
- **路径**: `/visits`
- **请求体**:
  ```json
  {
    "patientName": "李四",
    "gender": "男",
    "age": 30,
    "visitDate": "2023-10-25",
    "diagnosisId": 5,
    "drugs": [
      { "drugId": 101, "quantity": 2 }
    ]
  }
  ```
- **权限**: `DOCTOR`
- **副作用**: 创建记录，状态为 `SUBMITTED` (待发药)，触发 WebSocket 通知药师。

#### 2.5.2 获取就诊记录列表
- **方法**: `GET`
- **路径**: `/visits`
- **参数**: 
  - `status`: `SUBMITTED` (药师待办), `DRAFT`, `RETURNED`
  - `startDate`, `endDate`
  - `doctorId`: 查看特定医生的记录
- **权限**: `DOCTOR` (看自己的), `PHARMACIST` (看待发药的)

#### 2.5.3 药师发药 (Approve)
- **方法**: `POST`
- **路径**: `/visits/{id}/dispense`
- **权限**: `PHARMACIST`
- **副作用**: 扣减库存，状态变更为 `COMPLETED`。若库存不足返回错误。

#### 2.5.4 药师退回 (Return)
- **方法**: `POST`
- **路径**: `/visits/{id}/return`
- **请求体**: `{ "reason": "剂量错误" }`
- **权限**: `PHARMACIST`
- **副作用**: 状态变更为 `RETURNED`。

#### 2.5.5 医师修改重提
- **方法**: `PUT`
- **路径**: `/visits/{id}`
- **描述**: 仅当状态为 `RETURNED` 时允许修改。修改后状态变更为 `SUBMITTED`。
- **权限**: `DOCTOR`

---

### 2.6 库存盘点 (Inventory - Pharmacist Only)

#### 2.6.1 获取/生成当月盘点任务
- **方法**: `POST`
- **路径**: `/inventory-checks/generate`
- **参数**: `month` (e.g., "2023-10")
- **描述**: 若任务不存在则创建（快照当前理论库存），若存在则返回任务ID。
- **权限**: `PHARMACIST`

#### 2.6.2 获取盘点明细
- **方法**: `GET`
- **路径**: `/inventory-checks/{taskId}/details`
- **权限**: `PHARMACIST`

#### 2.6.3 提交盘点数据
- **方法**: `PUT`
- **路径**: `/inventory-checks/details/{detailId}`
- **请求体**:
  ```json
  {
    "actualStock": 98,
    "remark": "破损2瓶"
  }
  ```
- **权限**: `PHARMACIST`

#### 2.6.4 完成盘点任务
- **方法**: `POST`
- **路径**: `/inventory-checks/{taskId}/complete`
- **权限**: `PHARMACIST`
- **校验**: 检查是否所有明细都已录入。

#### 2.6.5 查询未完成的盘点任务 (逾期检查)
- **方法**: `GET`
- **路径**: `/inventory-checks/pending`
- **权限**: `PHARMACIST`

---

### 2.7 统计报表 (Stats)

#### 2.7.1 药品进销存月报
- **方法**: `GET`
- **路径**: `/stats/drugs`
- **参数**: `month` (yyyy-MM)
- **响应**: 包含期初、购进、使用、期末、盘点数据。

#### 2.7.2 运营月报 (人数/费用)
- **方法**: `GET`
- **路径**: `/stats/operations`
- **参数**: `month` (yyyy-MM)

#### 2.7.3 导出报表 (文件下载)
- **方法**: `GET`
- **路径**: `/stats/export`
- **参数**: `type` (drugs/operations), `month`
- **响应**: Binary Stream (Excel file)

---

### 2.8 实时通信 (WebSocket)

- **Endpoint**: `/ws`
- **Topic**: `/topic/pharmacist/notifications`
- **Payload**: `{ "type": "NEW_VISIT", "visitId": 123, "message": "有新的处方待处理" }`

---

## 3. 性能与安全考量

### 3.1 安全性
- **密码存储**: 使用 BCrypt 加密存储。
- **Token**: 使用 JWT，设置合理的过期时间（如 24 小时），并提供 Refresh Token 机制（可选）。
- **CORS**: 严格配置跨域白名单。
- **输入校验**: 后端对所有输入参数进行严格校验（如 SQL 注入防护、XSS 防护）。

### 3.2 性能优化
- **数据库索引**: 对 `username`, `drug.name`, `visit_date`, `status` 等高频查询字段建立索引。
- **并发控制**: 发药扣库存时使用数据库行锁或乐观锁 (`update drugs set stock = stock - ? where id = ? and stock >= ?`) 防止超卖。
- **缓存**: 对不常变动的 `DiagnosisType` 或药品列表可使用 Redis 缓存（视数据量而定，本项目数据量可能较小，暂不需要）。

### 3.3 扩展性
- **接口版本**: URL 包含 `/v1`，便于未来升级。
- **文件服务**: 预留文件上传接口，未来可扩展电子病历附件或药品图片。

## 4. 测试用例示例 (部分)

| ID | 接口 | 场景 | 预期结果 |
| :--- | :--- | :--- | :--- |
| TC01 | POST /auth/login | 用户名密码正确 | 200, 返回 Token |
| TC02 | POST /auth/login | 密码错误 | 401, 认证失败 |
| TC03 | POST /visits | 医师提交完整处方 | 200, 状态变为 SUBMITTED |
| TC04 | POST /visits/{id}/dispense | 库存充足 | 200, 状态 COMPLETED, 库存减少 |
| TC05 | POST /visits/{id}/dispense | 库存不足 | 400, 提示库存不足 |
| TC06 | POST /inventory-checks/generate | 月末生成任务 | 200, 返回任务ID和明细列表 |
