# 医药协同药品出入库管理系统

基于 Spring Boot + PyQt6 的四角色药品出入库管理系统，支持医生开处方、药师发药、库存管理、采购计划、统计报表等功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Java 17, Spring Boot 3.5.9, MyBatis Plus 3.5.5, JWT, EasyExcel 3.3.3 |
| 客户端 | Python 3, PyQt6 桌面应用 |
| 数据库 | MySQL 8.0 |

## 四种角色

| 角色 | 权限 |
|------|------|
| **ADMIN** | 用户管理、操作日志 |
| **DOCTOR** | 就诊记录、处方开具、药品查询、统计报表 |
| **PHARMACIST** | 发药、退药、库存盘点、药品管理、采购入库、采购计划、统计报表 |
| **ROOT** | 拥有 DOCTOR + PHARMACIST 全部权限 |

## 核心功能

- **处方流程**：医生开具 → 药师发药（FIFO 批次扣减）或退回并注明原因
- **库存管理**：多批次药品库存，使用 `SELECT ... FOR UPDATE` 并发控制
- **库存盘点**：月度库存盘点，自动计算理论库存与实际库存差异，支持差异追踪与库存自动调整
- **采购计划**：月度采购计划，自动填充药品数据，支持数量填写、完成/重新打开/删除，Excel 导出
- **药品采购**：批量采购入库，自动生成批号（`YYYYMMDD_HH_mm_drugId`）
- **生产厂家追踪**：按批次记录生产厂家，支持历史厂家选择对话框
- **统计报表**：按月/年统计药品出入库、操作量、工作量汇总，全部支持 Excel 导出
- **通知系统**：实时角标计数和弹窗通知待处理处方
- **键盘导航**：全局键盘操作，Enter 链式切换、下拉导航、Alt 快捷键、输入提示

## 数据库初始化

项目使用 MySQL 8.0，数据库脚本统一放在 `database/` 目录。

首次部署时执行 `database/init.sql` 即可完成建表和种子数据导入：

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS drug_in_out DEFAULT CHARACTER SET utf8mb4;"
mysql -u root -p drug_in_out < database/init.sql
```

> **注意**：`init.sql` 是基础 schema，生产环境的表结构可能包含额外字段（如 `machine_id`、`role`、`operate_data`）。若需与生产对齐，请自行执行对应的增量 DDL。


## 快速开始

```bash
# 1. 后端
cd DurgInOutSystem
./mvnw spring-boot:run

# 2. 客户端
cd client
python -m venv .venv
.venv\Scripts\pip install PyQt6 requests

# 设置后端地址（默认 http://localhost:8080）
set API_BASE_URL=http://your-server:8080

.venv\Scripts\python main.py
```

默认管理员账号：`admin` / `admin123`

## 客户端打包

使用 PyInstaller 将 PyQt6 客户端打包为独立可执行文件：

```bash
cd client

# 安装打包工具
.venv\Scripts\pip install pyinstaller

# 打包为单文件 exe（输出到 dist/ 目录）
.venv\Scripts\pyinstaller --onefile --windowed --name "药品出入库管理系统" main.py
```

可选参数说明：

| 参数 | 作用 |
|------|------|
| `--onefile` | 打包为单个 exe 文件 |
| `--windowed` | 无控制台窗口（GUI 应用） |
| `--name` | 输出文件名 |
| `--icon=app.ico` | 指定程序图标 |
| `--add-data` | 打包额外资源文件 |

打包完成后在 `client/dist/` 目录找到 exe，分发给用户即可运行。

## 项目结构

```
├── DurgInOutSystem/    # Spring Boot 后端
│   └── src/main/java/com/gcky/durginoutsystem/
│       ├── controller/     # REST API 控制器
│       ├── service/        # 业务逻辑
│       ├── mapper/         # MyBatis Plus 数据访问
│       ├── entity/         # 数据库实体 + DTO + Excel DTO
│       └── config/         # 权限拦截器、CORS、MyBatis 配置
├── client/             # PyQt6 桌面客户端
│   ├── main.py             # 入口文件
│   ├── ui/                 # 视图、组件、样式
│   └── utils/              # API 客户端
└── database/           # 数据库脚本
    └── init.sql             # 初始建表 + 种子数据
```