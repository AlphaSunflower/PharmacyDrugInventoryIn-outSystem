# 医药协同药品出入库管理系统

Pharmacy Drug Inventory Management System — a four-role system supporting doctors writing prescriptions, pharmacists dispensing drugs, managing inventory/purchases, and administrators managing users and audit logs.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Java 17, Spring Boot 3.5.9, MyBatis Plus 3.5.5, JWT, EasyExcel 3.3.3 |
| Frontend | Python 3, PyQt6 Desktop GUI |
| Database | MySQL 8.0 |

## Four Roles

| Role | Capabilities |
|------|-------------|
| **ADMIN** | User management, operation logs |
| **DOCTOR** | Patient visits, prescriptions, drug lookup, statistics |
| **PHARMACIST** | Dispense drugs, inventory check, drug management, purchase, purchase plan, statistics |
| **ROOT** | All DOCTOR + PHARMACIST privileges |

## Key Features

- **Prescription workflow**: Doctor submits → Pharmacist dispenses (FIFO batch deduction) or returns with reason
- **Inventory management**: Multi-batch drug stock with `SELECT ... FOR UPDATE` concurrency control
- **Inventory check**: Monthly stock counting with discrepancy tracking and auto-adjustment
- **Purchase plan**: Monthly procurement planning with automatic drug data population, quantity filling, completion, and Excel export
- **Drug purchase**: Batch purchase registration with automatic batch number generation (`YYYYMMDD_HH_mm_drugId`)
- **Manufacturer tracking**: Per-batch manufacturer field with historical vendor selection dialog
- **Statistics**: Monthly/yearly drug in/out reports, operation stats, workload summaries — all with Excel export
- **Notification system**: Real-time badge counts and toast notifications for pending prescriptions
- **Keyboard navigation**: Full keyboard support with Enter chains, dropdown navigation, Alt shortcuts, and tooltip hints

## Quick Start

```bash
# 1. Database
mysql -u root -p < database/init.sql
mysql -u root -p < database/update_purchase_plan.sql  # migration

# 2. Backend
cd DurgInOutSystem
./mvnw spring-boot:run

# 3. Client
cd client
pip install PyQt6 requests
python main.py
```

Default admin account: `admin` / `admin123`

## Project Structure

```
├── DurgInOutSystem/    # Spring Boot backend
│   └── src/main/java/com/gcky/durginoutsystem/
│       ├── controller/     # REST API controllers
│       ├── service/        # Business logic
│       ├── mapper/         # MyBatis Plus mappers
│       ├── entity/         # DB entities + DTOs + Excel DTOs
│       └── config/         # Auth interceptor, CORS, MyBatis config
├── client/             # PyQt6 desktop client
│   ├── main.py             # Entry point
│   ├── ui/                 # Views, components, styles
│   └── utils/              # API client
└── database/           # SQL schema + migrations
```
