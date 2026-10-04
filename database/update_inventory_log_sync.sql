ALTER TABLE pharmacy_db.inventory_check_details
    ADD COLUMN log_content VARCHAR(255) NULL COMMENT '盘点日志内容' AFTER actual_amount;
