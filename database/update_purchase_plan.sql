-- =============================================
-- 采购计划模块 + 生产厂家字段 数据库迁移
-- =============================================

-- 1. drug_batches 表新增生产厂家字段
ALTER TABLE drug_batches
    ADD COLUMN manufacturer VARCHAR(255) DEFAULT NULL COMMENT '生产厂家';

-- 2. 新建采购计划主表
CREATE TABLE IF NOT EXISTS purchase_plans (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '计划ID',
    month       VARCHAR(7)   NOT NULL UNIQUE COMMENT '计划月份 (YYYY-MM)',
    status      VARCHAR(20)  NOT NULL DEFAULT 'PENDING' COMMENT '状态: PENDING/COMPLETED',
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品采购计划表';

-- 3. 新建采购计划明细表
CREATE TABLE IF NOT EXISTS purchase_plan_details (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    plan_id         BIGINT        NOT NULL COMMENT '计划ID',
    drug_id         BIGINT        NOT NULL COMMENT '药品ID',
    spec            VARCHAR(100)  COMMENT '规格（快照）',
    unit            VARCHAR(50)   COMMENT '单位（快照）',
    purchase_price  DECIMAL(10,2) COMMENT '进货价（取自最新批次）',
    manufacturer    VARCHAR(255)  COMMENT '生产厂家（可编辑）',
    planned_quantity INT          DEFAULT NULL COMMENT '计划数量（药师必填）',
    created_at      DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (plan_id) REFERENCES purchase_plans(id),
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购计划明细表';
