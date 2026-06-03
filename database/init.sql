create table pharmacy_db.diagnosis_types
(
    id     bigint auto_increment comment '诊断ID'
        primary key,
    name   varchar(100) not null comment '诊断名称',
    remark varchar(255) null comment '备注',
    constraint name
        unique (name)
)
    comment '诊断类型表' charset = utf8mb4;

create table pharmacy_db.drugs
(
    id             bigint auto_increment comment '药品ID'
        primary key,
    name           varchar(100)                             not null comment '药品名称',
    spec           varchar(50)                              null comment '规格',
    unit           varchar(20)                              null comment '单位',
    price          decimal(10, 2) default 0.00              null comment '单价',
    stock_quantity int            default 0                 null comment '当前库存数量',
    is_deleted     tinyint        default 0                 null comment '是否删除: 0-否, 1-是',
    created_at     datetime       default CURRENT_TIMESTAMP null comment '创建时间',
    updated_at     datetime       default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '更新时间'
)
    comment '药品表' charset = utf8mb4;

create table pharmacy_db.drug_batches
(
    id               bigint auto_increment comment '批次ID'
        primary key,
    drug_id          bigint                             not null comment '关联药品ID',
    batch_no         varchar(50)                        null comment '批次号(可选，如生产批号)',
    price            decimal(10, 2)                     not null comment '本批次单价/进价',
    stock_quantity   int                                not null comment '本批次剩余库存',
    initial_quantity int                                not null comment '本批次初始数量(用于统计)',
    production_date  date                               null comment '生产日期',
    expiry_date      date                               null comment '有效期',
    created_at       datetime default CURRENT_TIMESTAMP null comment '入库时间',
    manufacturer     varchar(255)                       null comment '生产厂家',
    constraint drug_batches_ibfk_1
        foreign key (drug_id) references pharmacy_db.drugs (id)
)
    comment '药品库存批次表' charset = utf8mb4;

create index idx_created_at
    on pharmacy_db.drug_batches (created_at);

create index idx_drug_stock
    on pharmacy_db.drug_batches (drug_id, stock_quantity);

create table pharmacy_db.inventory_check_tasks
(
    id           bigint auto_increment comment '任务ID'
        primary key,
    month        varchar(7)                                              not null comment '盘点月份 (YYYY-MM)',
    status       enum ('PENDING', 'COMPLETED') default 'PENDING'         null comment '状态: 进行中/已完成',
    created_at   datetime                      default CURRENT_TIMESTAMP null comment '创建时间',
    completed_at datetime                                                null comment '完成时间',
    constraint month
        unique (month)
)
    comment '库存盘点任务表' charset = utf8mb4;

create table pharmacy_db.inventory_check_details
(
    id            bigint auto_increment comment '盘点明细ID'
        primary key,
    task_id       bigint         not null comment '任务ID',
    drug_id       bigint         not null comment '药品ID',
    system_stock  int            not null comment '系统理论库存',
    actual_stock  int            null comment '实际盘点库存',
    discrepancy   int            null comment '差异数量 (实际 - 理论)',
    remark        varchar(255)   null comment '备注',
    actual_amount decimal(10, 2) null comment '期末实盘金额',
    constraint inventory_check_details_ibfk_1
        foreign key (task_id) references pharmacy_db.inventory_check_tasks (id),
    constraint inventory_check_details_ibfk_2
        foreign key (drug_id) references pharmacy_db.drugs (id)
)
    comment '库存盘点明细表' charset = utf8mb4;

create index idx_drug_id
    on pharmacy_db.inventory_check_details (drug_id);

create index idx_task_id
    on pharmacy_db.inventory_check_details (task_id);

create table pharmacy_db.purchase_details
(
    id            bigint auto_increment comment '购进记录ID'
        primary key,
    drug_id       bigint                             not null comment '药品ID',
    quantity      int                                not null comment '购进数量',
    unit          varchar(20)                        null comment '单位',
    price         decimal(10, 2)                     not null comment '购进单价',
    total_amount  decimal(10, 2)                     not null comment '购进总金额',
    purchase_date date                               not null comment '购进日期',
    created_at    datetime default CURRENT_TIMESTAMP null comment '记录创建时间',
    batch_id      bigint                             null comment '关联批次ID',
    constraint purchase_details_ibfk_1
        foreign key (drug_id) references pharmacy_db.drugs (id)
)
    comment '药品购进明细表' charset = utf8mb4;

create index drug_id
    on pharmacy_db.purchase_details (drug_id);

create index idx_batch_id
    on pharmacy_db.purchase_details (batch_id);

create index idx_purchase_date
    on pharmacy_db.purchase_details (purchase_date);

create table pharmacy_db.purchase_plans
(
    id         bigint auto_increment comment '计划ID'
        primary key,
    month      varchar(7)                            not null comment '计划月份 (YYYY-MM)',
    status     varchar(20) default 'PENDING'         not null comment '状态: PENDING/COMPLETED',
    created_at datetime    default CURRENT_TIMESTAMP null comment '创建时间',
    updated_at datetime    default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '更新时间',
    constraint month
        unique (month)
)
    comment '药品采购计划表' charset = utf8mb4;

create table pharmacy_db.purchase_plan_details
(
    id               bigint auto_increment comment '明细ID'
        primary key,
    plan_id          bigint                             not null comment '计划ID',
    drug_id          bigint                             not null comment '药品ID',
    spec             varchar(100)                       null comment '规格（快照）',
    unit             varchar(50)                        null comment '单位（快照）',
    purchase_price   decimal(10, 2)                     null comment '进货价（取自最新批次）',
    manufacturer     varchar(255)                       null comment '生产厂家（可编辑）',
    planned_quantity int                                null comment '计划数量（药师必填）',
    created_at       datetime default CURRENT_TIMESTAMP null comment '创建时间',
    constraint purchase_plan_details_ibfk_1
        foreign key (plan_id) references pharmacy_db.purchase_plans (id),
    constraint purchase_plan_details_ibfk_2
        foreign key (drug_id) references pharmacy_db.drugs (id)
)
    comment '采购计划明细表' charset = utf8mb4;

create index drug_id
    on pharmacy_db.purchase_plan_details (drug_id);

create index plan_id
    on pharmacy_db.purchase_plan_details (plan_id);

create table pharmacy_db.users
(
    id         bigint auto_increment comment '用户ID'
        primary key,
    username   varchar(50)                                    not null comment '用户名',
    password   varchar(255)                                   not null comment '加密密码',
    real_name  varchar(50)                                    null comment '真实姓名',
    role       enum ('ADMIN', 'DOCTOR', 'PHARMACIST', 'ROOT') not null comment '角色',
    status     tinyint  default 1                             null comment '状态: 1-启用, 0-停用',
    created_at datetime default CURRENT_TIMESTAMP             null comment '创建时间',
    machine_id varchar(255)                                   null comment '机器码',
    constraint username
        unique (username)
)
    comment '用户表' charset = utf8mb4;

create table pharmacy_db.operation_logs
(
    id           bigint auto_increment comment '日志ID'
        primary key,
    user_id      bigint                             null comment '操作人ID',
    action       varchar(255)                       not null comment '操作描述',
    created_at   datetime default CURRENT_TIMESTAMP null comment '操作时间',
    role         varchar(10)                        null comment '角色',
    operate_data varchar(100)                       null comment '操作数据',
    constraint operation_logs_ibfk_1
        foreign key (user_id) references pharmacy_db.users (id)
)
    comment '操作日志表' charset = utf8mb4;

create index idx_created_at
    on pharmacy_db.operation_logs (created_at);

create index idx_user_id
    on pharmacy_db.operation_logs (user_id);

create table pharmacy_db.patient_visits
(
    id               bigint auto_increment comment '就诊ID'
        primary key,
    doctor_id        bigint                                                                                     not null comment '医师ID',
    patient_name     varchar(50)                                                                                not null comment '患者姓名',
    gender           varchar(10)                                                                                null comment '性别',
    age              int                                                                                        null comment '年龄',
    custom_diagnosis varchar(255)                                                                               null comment '自定义诊断内容',
    diagnosis_id     bigint                                                                                     null comment '诊断类型ID',
    department       varchar(20)                                                                                null comment '部门',
    visit_date       date                                                                                       not null comment '就诊日期',
    status           enum ('DRAFT', 'SUBMITTED', 'RETURNED', 'COMPLETED', 'CANCELED') default 'DRAFT'           null comment '状态: 草稿/待发药/已退回/已完成/已取消',
    return_reason    varchar(255)                                                                               null comment '退回原因',
    created_at       datetime                                                         default CURRENT_TIMESTAMP null comment '创建时间',
    updated_at       datetime                                                         default CURRENT_TIMESTAMP null on update CURRENT_TIMESTAMP comment '更新时间',
    constraint patient_visits_ibfk_1
        foreign key (doctor_id) references pharmacy_db.users (id),
    constraint patient_visits_ibfk_2
        foreign key (diagnosis_id) references pharmacy_db.diagnosis_types (id)
)
    comment '患者就诊记录表' charset = utf8mb4;

create index diagnosis_id
    on pharmacy_db.patient_visits (diagnosis_id);

create index idx_doctor_id
    on pharmacy_db.patient_visits (doctor_id);

create index idx_status
    on pharmacy_db.patient_visits (status);

create index idx_visit_date
    on pharmacy_db.patient_visits (visit_date);

create index idx_machine_id
    on pharmacy_db.users (machine_id);

create table pharmacy_db.visit_drugs
(
    id       bigint auto_increment comment '处方明细ID'
        primary key,
    visit_id bigint         not null comment '就诊ID',
    drug_id  bigint         not null comment '药品ID',
    quantity int            not null comment '数量',
    amount   decimal(10, 2) not null comment '金额',
    price    decimal(10, 2) null comment '当时单价',
    constraint visit_drugs_ibfk_1
        foreign key (visit_id) references pharmacy_db.patient_visits (id),
    constraint visit_drugs_ibfk_2
        foreign key (drug_id) references pharmacy_db.drugs (id)
)
    comment '就诊处方药品明细表' charset = utf8mb4;

create index idx_drug_id
    on pharmacy_db.visit_drugs (drug_id);

create index idx_visit_id
    on pharmacy_db.visit_drugs (visit_id);

