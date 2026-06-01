-- 1. 新增药品批次表
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

-- 2. 购进明细表增加 batch_id 字段
ALTER TABLE purchase_details ADD COLUMN batch_id BIGINT COMMENT '关联批次ID';
-- 如果需要外键约束 (建议加上，但需确保顺序)
-- ALTER TABLE purchase_details ADD CONSTRAINT fk_purchase_batch FOREIGN KEY (batch_id) REFERENCES drug_batches(id);
