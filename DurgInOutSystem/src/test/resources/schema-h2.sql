CREATE TABLE IF NOT EXISTS drugs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    spec VARCHAR(50),
    unit VARCHAR(20),
    price DECIMAL(10,2) DEFAULT 0,
    stock_quantity INT DEFAULT 0,
    is_deleted INT DEFAULT 0,
    manufacturer VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drug_batches (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    drug_id BIGINT NOT NULL,
    batch_no VARCHAR(100),
    price DECIMAL(10,2) DEFAULT 0,
    stock_quantity INT DEFAULT 0,
    initial_quantity INT DEFAULT 0,
    manufacturer VARCHAR(200),
    production_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_visits (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id BIGINT,
    patient_name VARCHAR(100),
    visit_date DATE,
    status VARCHAR(20) DEFAULT 'SUBMITTED',
    diagnosis_id BIGINT,
    custom_diagnosis VARCHAR(200),
    return_reason VARCHAR(500),
    gender VARCHAR(10),
    age INT,
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS visit_drugs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    visit_id BIGINT NOT NULL,
    drug_id BIGINT NOT NULL,
    quantity INT DEFAULT 0,
    amount DECIMAL(10,2),
    price DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS diagnosis_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100),
    real_name VARCHAR(50),
    role VARCHAR(20),
    status INT DEFAULT 1,
    machine_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_check_tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    month VARCHAR(7),
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_check_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    drug_id BIGINT NOT NULL,
    system_stock INT DEFAULT 0,
    actual_stock INT,
    discrepancy INT,
    actual_amount DECIMAL(10,2),
    remark VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS purchase_plans (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    month VARCHAR(7),
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_plan_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plan_id BIGINT NOT NULL,
    drug_id BIGINT NOT NULL,
    spec VARCHAR(50),
    unit VARCHAR(20),
    purchase_price DECIMAL(10,2),
    manufacturer VARCHAR(200),
    planned_quantity INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    drug_id BIGINT,
    batch_id BIGINT,
    quantity INT,
    unit VARCHAR(20),
    price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    purchase_date DATE,
    manufacturer VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    operation VARCHAR(200),
    operate_data VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
