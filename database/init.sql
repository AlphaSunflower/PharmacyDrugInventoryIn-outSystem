-- 创建数据库
CREATE DATABASE IF NOT EXISTS pharmacy_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE pharmacy_db;

-- 1. 用户表 (User)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '加密密码',
    real_name VARCHAR(50) COMMENT '真实姓名',
    role ENUM('ADMIN', 'DOCTOR', 'PHARMACIST') NOT NULL COMMENT '角色',
    status TINYINT DEFAULT 1 COMMENT '状态: 1-启用, 0-停用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 药品表 (Drug)
CREATE TABLE IF NOT EXISTS drugs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '药品ID',
    name VARCHAR(100) NOT NULL COMMENT '药品名称',
    spec VARCHAR(50) COMMENT '规格',
    unit VARCHAR(20) COMMENT '单位',
    price DECIMAL(10, 2) DEFAULT 0.00 COMMENT '单价',
    stock_quantity INT DEFAULT 0 COMMENT '当前库存数量',
    is_deleted TINYINT DEFAULT 0 COMMENT '是否删除: 0-否, 1-是',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品表';

-- 3. 诊断类型表 (DiagnosisType)
CREATE TABLE IF NOT EXISTS diagnosis_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '诊断ID',
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '诊断名称',
    remark VARCHAR(255) COMMENT '备注'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='诊断类型表';

-- 4. 购进明细表 (PurchaseDetail)
CREATE TABLE IF NOT EXISTS purchase_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '购进记录ID',
    drug_id BIGINT NOT NULL COMMENT '药品ID',
    quantity INT NOT NULL COMMENT '购进数量',
    unit VARCHAR(20) COMMENT '单位',
    price DECIMAL(10, 2) NOT NULL COMMENT '购进单价',
    total_amount DECIMAL(10, 2) NOT NULL COMMENT '购进总金额',
    purchase_date DATE NOT NULL COMMENT '购进日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    batch_id BIGINT COMMENT '关联批次ID',
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品购进明细表';

-- 5. 就诊记录表 (PatientVisit)
CREATE TABLE IF NOT EXISTS patient_visits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '就诊ID',
    doctor_id BIGINT NOT NULL COMMENT '医师ID',
    patient_name VARCHAR(50) NOT NULL COMMENT '患者姓名',
    gender VARCHAR(10) COMMENT '性别',
    age INT COMMENT '年龄',
    diagnosis_id BIGINT COMMENT '诊断类型ID',
    department VARCHAR(50) COMMENT '部门: 本厂/外包/领导拿药',
    visit_date DATE NOT NULL COMMENT '就诊日期',
    status ENUM('DRAFT', 'SUBMITTED', 'RETURNED', 'COMPLETED') DEFAULT 'DRAFT' COMMENT '状态: 草稿/待发药/已退回/已完成',
    return_reason VARCHAR(255) COMMENT '退回原因',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    FOREIGN KEY (diagnosis_id) REFERENCES diagnosis_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者就诊记录表';

-- 6. 就诊处方明细表 (VisitDrug)
CREATE TABLE IF NOT EXISTS visit_drugs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '处方明细ID',
    visit_id BIGINT NOT NULL COMMENT '就诊ID',
    drug_id BIGINT NOT NULL COMMENT '药品ID',
    quantity INT NOT NULL COMMENT '数量',
    amount DECIMAL(10, 2) NOT NULL COMMENT '金额',
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id),
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='就诊处方药品明细表';

-- 7. 盘点任务表 (InventoryCheckTask)
CREATE TABLE IF NOT EXISTS inventory_check_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    month VARCHAR(7) NOT NULL UNIQUE COMMENT '盘点月份 (YYYY-MM)',
    status ENUM('PENDING', 'COMPLETED') DEFAULT 'PENDING' COMMENT '状态: 进行中/已完成',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at DATETIME COMMENT '完成时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存盘点任务表';

-- 8. 盘点明细表 (InventoryCheckDetail)
CREATE TABLE IF NOT EXISTS inventory_check_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '盘点明细ID',
    task_id BIGINT NOT NULL COMMENT '任务ID',
    drug_id BIGINT NOT NULL COMMENT '药品ID',
    system_stock INT NOT NULL COMMENT '系统理论库存',
    actual_stock INT COMMENT '实际盘点库存',
    actual_amount DECIMAL(10, 2) DEFAULT 0.00 COMMENT '期末实盘金额',
    discrepancy INT COMMENT '差异数量 (实际 - 理论)',
    remark VARCHAR(255) COMMENT '备注',
    FOREIGN KEY (task_id) REFERENCES inventory_check_tasks(id),
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存盘点明细表';

-- 9. 操作日志表 (OperationLog)
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id BIGINT COMMENT '操作人ID',
    action VARCHAR(255) NOT NULL COMMENT '操作描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 10. 药品批次表 (DrugBatch)
CREATE TABLE IF NOT EXISTS drug_batches (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '批次ID',
    drug_id         BIGINT          NOT NULL COMMENT '关联药品ID',
    batch_no        VARCHAR(50)     NULL COMMENT '批次号(可选，如生产批号)',
    price           DECIMAL(10, 2)  NOT NULL COMMENT '本批次单价/进价',
    stock_quantity  INT             NOT NULL COMMENT '本批次剩余库存',
    initial_quantity INT            NOT NULL COMMENT '本批次初始数量(用于统计)',
    production_date DATE            NULL COMMENT '生产日期',
    expiry_date     DATE            NULL COMMENT '有效期',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_drug_stock (drug_id, stock_quantity),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品库存批次表';

-- 初始化数据

-- 1. 初始化管理员账号 (密码: admin123)
-- 注意: 实际生产环境应存储加密密码，此处仅为示例
INSERT INTO users (username, password, real_name, role) VALUES 
('admin', 'admin123', '系统管理员', 'ADMIN');

-- 2. 初始化一些诊断类型
INSERT INTO diagnosis_types (name, remark) VALUES 
('上呼吸道感染', '常见感冒症状'),
('急性胃肠炎', '腹痛腹泻'),
('高血压', '慢性病'),
('过敏性皮炎', '皮肤过敏'),
('外伤', '各类外伤处理');

-- 3. 初始化一些药品
INSERT INTO drugs (name, spec, unit, price, stock_quantity) VALUES 
('阿莫西林胶囊', '0.25g*24粒', '盒', 15.50, 100),
('布洛芬缓释胶囊', '0.3g*20粒', '盒', 22.00, 50),
('板蓝根颗粒', '10g*20袋', '包', 12.00, 200),
('蒙脱石散', '3g*10袋', '盒', 18.00, 80);
