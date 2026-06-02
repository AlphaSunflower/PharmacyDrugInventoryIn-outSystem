# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

药品出入库管理系统 — a four-role pharmacy inventory system (ADMIN, DOCTOR, PHARMACIST, ROOT). Supports doctors writing prescriptions, pharmacists dispensing drugs and managing inventory/purchases, and admins managing users and audit logs. ROOT has both doctor and pharmacist privileges.

## Tech Stack

- **Backend**: Java 17, Spring Boot 3.5.9, MyBatis Plus 3.5.5, MySQL, JWT (jjwt 0.11.5), EasyExcel 3.3.3
- **Client**: Python 3, PyQt6 desktop GUI
- **Database**: MySQL 8.0 (schema in `database/init.sql`)

## Project Structure

```
DurgInOutSystem/src/main/java/com/gcky/durginoutsystem/
  controller/          # REST controllers under /api/v1 (thin, delegate to services)
  service/             # Service interfaces + impl/ subpackage
    StatsService       # All stats calculation logic (drug stats, operations, monthly/yearly summary)
    DrugStockService   # Shared: recalculates drug total stock from batch sums
  mapper/              # MyBatis Plus BaseMapper interfaces
  entity/              # DB entities + dto/ + excel/ subpackages
  common/Result.java   # Unified response: {code, message, data}
  config/              # AuthInterceptor (JWT + RBAC), WebMvcConfig (CORS), MybatisPlusConfig
  utils/JwtUtil.java   # JWT: secret from config, HS256, 24h expiry, constructor injection
  annotation/          # @Log (audit), @RequireRole (RBAC)
  aspect/LogAspect.java
  exception/           # BusinessException (400), GlobalExceptionHandler (400/500)

client/
  main.py              # Entry: LoginWindow + machine-id auto-login
  ui/                  # main_window, admin_views, doctor_views, pharmacist_views, components, style_constants
  utils/api_client.py  # requests.Session() singleton with (5,15)s timeout, BASE_URL from env
database/
  init.sql             # Full schema + seed data
  update_*.sql         # Migration scripts
```

## Backend Architecture

**Controller → Service → Mapper** (MyBatis Plus), with these cross-cutting concerns:

- **Auth**: `AuthInterceptor` validates JWT on all `/api/v1/**` except login/auto-login. Extracts userId/role/username into request attributes. `@RequireRole` annotation on controllers for RBAC. ROOT role bypasses all role checks.
- **Concurrency**: `DrugBatchMapper.selectBatchesForUpdate()` uses `SELECT ... FOR UPDATE` for FIFO batch deduction. `incrementStock()` does atomic DB-side `stock_quantity = stock_quantity + ?`.
- **Error handling**: `BusinessException` for domain errors → HTTP 400. Generic `RuntimeException` → HTTP 500 (internal error, details not leaked).
- **Audit**: `@Log` AOP captures operation logs via `LogAspect`, reading userId from request attributes.
- **Stock**: `DrugStockService.updateDrugTotalStock()` recalculates `drugs.stock_quantity` as `SUM(drug_batches.stock_quantity)`.

### Key Endpoints

| Endpoint | Role | Purpose |
|----------|------|---------|
| `POST /auth/login` | none | Login, returns JWT |
| `POST /auth/auto-login` | none | Auto-login via machine ID |
| `GET /visits/notification-counts` | all | Returns pendingCount, returnedCount for badges |
| `POST /visits` | DOCTOR | Submit prescription |
| `POST /visits/{id}/dispense` | PHARMACIST | Dispense (FIFO batch deduction) |
| `POST /visits/{id}/return` | PHARMACIST | Return to doctor with reason |
| `GET /drugs` | DOCTOR/PHARMACIST | Drug list with batchList |
| `GET /stats/inventory-check` | DOCTOR/PHARMACIST | Inventory check report for a month |
| `POST /purchase-plans/generate` | PHARMACIST | Generate/get monthly purchase plan |
| `POST /purchase-plans/{id}/complete` | PHARMACIST | Complete purchase plan |
| `GET /stats/purchase-plan` | DOCTOR/PHARMACIST | Query purchase plan data |
| `GET /stats/purchase-plan/export` | DOCTOR/PHARMACIST | Export purchase plan to Excel |
| `PUT /drugs/batch/{id}` | PHARMACIST | Update batch info (manufacturer, etc.) |

## Config

Configuration uses **YAML with Spring profiles**:

```
resources/
├── application.yml          # Shared config (tracked in git, no secrets)
├── application-local.yml    # Local dev (gitignored, real credentials)
└── application-dev.yml      # Remote server (gitignored, real credentials)
```

- Default profile: `local`
- `jwt.secret` injected via `@Value("${jwt.secret}")` — set per profile
- DB credentials via `${DB_URL}`, `${DB_USERNAME}`, `${DB_PASSWORD}` env vars with per-profile overrides

## Client Architecture

- **API client**: `requests.Session()` singleton with (5,15)s timeout, `BASE_URL` from `API_BASE_URL` env var (default localhost)
- **Notification system**: MainWindow polls `/visits/notification-counts` every 5s. `BadgedSidebarButton` shows red ●N overlay on sidebar. `ToastNotification` pops up bottom-right on new items, auto-dismisses 4s, click navigates to relevant view.
- **Cross-view refresh**: `MainWindow.stock_changed` signal emitted after dispense/purchase. DrugManageView and DrugQueryView connect to auto-refresh.
- **Poling**: DispenseView 8s, VisitHistoryView 8s. Other views refresh on showEvent or manual action.
- **Role-based menus**: ROOT gets 9 views (added 采购计划), PHARMACIST gets 7 views. DOCTOR gets 4 views, ADMIN gets 2 views.
- **Keyboard shortcuts**: Global keyboard navigation with Enter chains, Alt+←→ field switching, ↑↓ popup selection with highlight, ESC to cancel. Tooltip hints on all inputs.

## Build & Run

```bash
# Backend
cd DurgInOutSystem
./mvnw clean compile       # Build
./mvnw test                # Run tests
./mvnw spring-boot:run     # Run

# Client
cd client
pip install PyQt6 requests
python main.py             # Set API_BASE_URL env var for remote server

# Database init
mysql -u root -p < database/init.sql
```

### UI Components (components.py)

- **ModernTable** — unified table widget with built-in hover highlight, rounded headers, alternating row colors. All views use this instead of duplicating style_table().
- **BadgedSidebarButton** — sidebar button with red QLabel overlay showing ●N badge count
- **ToastNotification** — bottom-right popup with 300ms fade-out animation, clickable to navigate
- **ModernInputDialog** — styled replacement for QInputDialog.getText()

## Important Notes

- Plaintext passwords are intentional per project requirements — no bcrypt needed.
- JWT secret and DB credentials are in gitignored profile YAML files (`application-local.yml`, `application-dev.yml`).
- Drug stock is a denormalized sum of batch stocks — always use `DrugStockService.updateDrugTotalStock()` after batch mutations.
- `FOR UPDATE` on batches in `dispense()` is per-drug (not batched across drugs) to avoid deadlocks.
- `BusinessException` (not `RuntimeException`) should be used for expected domain errors in services.
- StatsController is thin — all calculation logic is in `StatsServiceImpl`. Monthly and yearly summary share `calculateSummaryReport()`.
- The `@RequireRole` annotation supports both class-level and method-level. ROOT bypasses all checks.
- Purchase batch numbers are auto-generated as `YYYYMMDD_HH_mm_drugId` (e.g. `20260601_22_30_1`).
- **Purchase Plan module**: `PurchasePlanController` + `PurchasePlanService` follow the same pattern as InventoryCheck. Generate monthly plans, fill quantities, complete/reopen/delete. Export via `GET /stats/purchase-plan/export`.
- **Manufacturer field**: `drug_batches.manufacturer` tracks manufacturer per batch. Auto-filled from latest batch on drug selection, editable via dialog with historical vendor list. Covered in drug management, purchase, and purchase plan.
- **Keyboard navigation**: Enter chains for form field navigation, dropdown popup on focus, ↑↓ selection with highlight, Alt+Enter for custom actions, ESC to cancel. All inputs have tooltip hints. See `components.py` SearchableComboBox and ModernInputDialog.
