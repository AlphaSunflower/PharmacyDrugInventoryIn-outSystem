-- 3.移除 visit_drugs 表中的 batch_id 字段
-- 注意：如果该字段有外键约束，需要先删除外键约束
-- 假设外键名称可能为 fk_visit_drug_batch 或自动生成的名称，如果之前没加外键则直接 drop column

ALTER TABLE visit_drugs DROP COLUMN batch_id;

-- price 字段保留，用于记录成交单价
