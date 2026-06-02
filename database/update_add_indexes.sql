-- 补充索引和约束
-- 执行前请备份数据库

USE pharmacy_db;

-- 1. purchase_details.batch_id 索引和约束（原 update_to_batches.sql 中 FK 被注释掉）
ALTER TABLE purchase_details ADD INDEX idx_batch_id (batch_id);
-- 如果 FK 约束也缺失则取消下面注释恢复：
-- ALTER TABLE purchase_details ADD CONSTRAINT fk_purchase_batch FOREIGN KEY (batch_id) REFERENCES drug_batches(id);

-- 2. 常用查询列索引
ALTER TABLE purchase_details ADD INDEX idx_purchase_date (purchase_date);

ALTER TABLE patient_visits ADD INDEX idx_visit_date (visit_date);
ALTER TABLE patient_visits ADD INDEX idx_status (status);
ALTER TABLE patient_visits ADD INDEX idx_doctor_id (doctor_id);

ALTER TABLE operation_logs ADD INDEX idx_user_id (user_id);
ALTER TABLE operation_logs ADD INDEX idx_created_at (created_at);

ALTER TABLE visit_drugs ADD INDEX idx_visit_id (visit_id);
ALTER TABLE visit_drugs ADD INDEX idx_drug_id (drug_id);

ALTER TABLE inventory_check_details ADD INDEX idx_task_id (task_id);
ALTER TABLE inventory_check_details ADD INDEX idx_drug_id (drug_id);

-- 3. 用户表索引
ALTER TABLE users ADD INDEX idx_machine_id (machine_id);
