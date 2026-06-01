# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

药品出入库管理系统 (Pharmacy Drug Inventory In/Out System) — a three-role medical inventory system for clinic pharmacies. Supports doctors (writing prescriptions), pharmacists (dispensing drugs, inventory checks, purchasing), and admins (user management, audit logs).

## Tech Stack

- **Backend**: Java 17, Spring Boot 3.5.9, MyBatis Plus 3.5.5, MySQL, JWT (jjwt 0.11.5), EasyExcel 3.3.3
- **Client**: Python 3, PyQt6 desktop GUI
- **Database**: MySQL 8.0 (schema in `database/init.sql`)

## Project Structure

```
DurgInOutSystem/          # Spring Boot backend (Maven)
  src/main/java/com/gcky/durginoutsystem/
    controller/           # REST controllers (all under /api/v1)
    service/              # Service interfaces + impl/ subpackage
    mapper/               # MyBatis Plus mapper interfaces (no XML needed)
    entity/               # DB entities + dto/ + excel/ subpackages
    common/Result.java    # Unified response envelope: {code, message, data}
    config/               # MyBatis Plus pagination interceptor
    utils/JwtUtil.java    # JWT generation + validation (HS256, 24h expiry)
    annotation/Log.java   # @Log annotation for operation audit logging
    aspect/LogAspect.java # AOP aspect that auto-records operation logs
    exception/            # GlobalExceptionHandler (@RestControllerAdvice)

client/                   # PyQt6 desktop client
  main.py                 # Entry point: LoginWindow + auto-login via machine ID
  ui/                     # PyQt6 views (main_window, admin_views, doctor_views, pharmacist_views, components, style_constants)
  utils/api_client.py     # Singleton APIClient wrapping requests (BASE_URL, JWT, get/post/put/patch/delete)
  build/                  # PyInstaller build output
  dist/                   # Distribution .exe

database/                 # SQL scripts
  init.sql                # Full schema + seed data
  update_*.sql            # Migration scripts (batches, inventory, visit_drugs changes)
```

## Backend Architecture

Standard layered architecture: **Controller → Service (interface) → ServiceImpl → Mapper (MyBatis Plus)**

- Controllers are thin — extract userId/role from JWT via `JwtUtil`, delegate to services, return `Result<T>`.
- Services use `@Transactional` for multi-table operations (especially visit submission and drug dispensing).
- Mappers extend MyBatis Plus `BaseMapper<T>` — no manual SQL for basic CRUD. Complex queries use `QueryWrapper`.
- `@CrossOrigin` on all controllers.
- AOP logging via `@Log("description")` annotation on controller methods — automatically saves to `operation_logs` table.

### Key Domain Flows

**Prescription → Dispense cycle** (the core business flow):
1. Doctor submits visit (`POST /visits`, status → `SUBMITTED`)
2. Pharmacist sees pending visits, can dispense (`POST /visits/{id}/dispense` → FIFO batch deduction, status → `COMPLETED`) or return with reason (`POST /visits/{id}/return` → status → `RETURNED`)
3. Doctor can modify and resubmit returned visits (`PUT /visits/{id}`)

**Inventory**: Batch-based FIFO dispense (`drug_batches` table). Total stock in `drugs.stock_quantity` is a computed sum of batch stocks. Purchases create new batches. Inventory checks snapshot system stock vs physical count.

## Build & Run Commands

### Backend

```bash
# Build
cd DurgInOutSystem
./mvnw clean compile       # or: mvn clean compile

# Run tests
./mvnw test

# Package (JAR)
./mvnw clean package -DskipTests

# Run (Spring Boot)
./mvnw spring-boot:run
```

Database configuration is in `DurgInOutSystem/src/main/resources/application.properties`. Two connection profiles are present (remote server and localhost) — comment/uncomment as needed.

### Client

```bash
cd client

# Install dependencies
pip install PyQt6 requests

# Run
python main.py
```

The client's API base URL is hardcoded in `client/utils/api_client.py` (`APIClient.BASE_URL`). Switch between remote and localhost by commenting/uncommenting.

### Database

```bash
# Initialize database
mysql -u root -p < database/init.sql

# Apply migrations (run in order)
mysql -u root -p pharmacy_db < database/update_visit_drugs.sql
mysql -u root -p pharmacy_db < database/update_to_batches.sql
mysql -u root -p pharmacy_db < database/update_inventory_check.sql
mysql -u root -p pharmacy_db < database/remove_batch_id.sql
```

## API Convention

- Base: `/api/v1`
- Auth: `Authorization: Bearer <token>` header
- Response: `{ "code": 200, "message": "success", "data": {...} }`
- Pagination: `?page=1&size=10`, returns MyBatis Plus `Page` object serialized as JSON
- Status values for visits: `DRAFT`, `SUBMITTED`, `RETURNED`, `COMPLETED`
- Roles: `ADMIN`, `DOCTOR`, `PHARMACIST`
- JWT claims: `sub` (username), `role`, `userId`

## Important Notes

- The JWT secret (`JwtUtil.SECRET`) is hardcoded — do not use in production without rotating.
- DB credentials in `application.properties` are in plaintext — ensure these are secured before deployment.
- Client uses field injection (`@Autowired` on fields) rather than constructor injection throughout.
- Drug stock quantity in `drugs` table is a denormalized sum of `drug_batches.stock_quantity` — always call `updateDrugTotalStock()` after batch mutations.
- The `@Log` annotation on controllers has an atypical design — it records operation logs AFTER the method returns, and tries to extract userId from the JWT on the request context (which means it captures the logged-in user's actions but won't capture login events cleanly without special-casing).
