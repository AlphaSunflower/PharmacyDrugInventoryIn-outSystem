-- 2 visit_drugs 表增加 batch_id 和 price 字段
-- price 用于记录当时的实际单价，batch_id 用于绑定具体批次
ALTER TABLE visit_drugs ADD COLUMN batch_id BIGINT COMMENT '关联批次ID';
ALTER TABLE visit_drugs ADD COLUMN price DECIMAL(10, 2) COMMENT '当时单价';

-- 建议添加外键约束 (可选)
-- ALTER TABLE visit_drugs ADD CONSTRAINT fk_visit_drug_batch FOREIGN KEY (batch_id) REFERENCES drug_batches(id);
