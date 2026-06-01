-- 4 增加 inventory_check_details 表的 actual_amount 字段
ALTER TABLE inventory_check_details ADD COLUMN actual_amount DECIMAL(10, 2) COMMENT '期末实盘金额';
