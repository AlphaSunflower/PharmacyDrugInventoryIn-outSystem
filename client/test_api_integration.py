"""API endpoint integration test script - uses correct roles per endpoint"""
import requests
import json
import sys
import os

BASE = "http://localhost:8080/api/v1"
RESULTS = []

def test(name, method, path, expected_body_code=200, data=None, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, params=params, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, params=params, timeout=10)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=data, params=params, timeout=10)
        else:
            RESULTS.append(("FAIL", name, f"Unknown method: {method}"))
            return None

        body = {}
        try:
            body = resp.json()
        except:
            pass

        actual_code = body.get('code', 999) if body else 999
        status = "PASS" if actual_code == expected_body_code else "FAIL"

        detail = f"body.code={actual_code} (expected {expected_body_code})"
        if actual_code != expected_body_code:
            detail += f" | msg={body.get('message', 'N/A')}"

        RESULTS.append((status, name, detail))
        return body
    except requests.ConnectionError:
        RESULTS.append(("FAIL", name, "Connection refused - is server running?"))
        return None
    except Exception as e:
        RESULTS.append(("FAIL", name, str(e)[:200]))
        return None


# ========== Step 1: Create test users via admin ==========
print("Step 1: Setup test users via admin...")
body = test("Login admin", "POST", "/auth/login", 200,
            data={"username": "admin", "password": "admin123"})
ADMIN_TOKEN = body['data']['token'] if body and body.get('code') == 200 else None
if not ADMIN_TOKEN:
    print("FATAL: Cannot login as admin")
    sys.exit(1)

ts = __import__('time').strftime("%H%M%S")
# Create doctor test user
test("Create doctor user", "POST", "/users", 200, token=ADMIN_TOKEN,
     data={"username": f"_dr_{ts}", "password": "123", "realName": "Test Doctor", "role": "DOCTOR"})
# Create pharmacist test user
test("Create pharmacist user", "POST", "/users", 200, token=ADMIN_TOKEN,
     data={"username": f"_ph_{ts}", "password": "123", "realName": "Test Pharm", "role": "PHARMACIST"})
# Create root user
test("Create root user", "POST", "/users", 200, token=ADMIN_TOKEN,
     data={"username": f"_rt_{ts}", "password": "123", "realName": "Test Root", "role": "ROOT"})

# Login as each role
dr_body = test("Login doctor", "POST", "/auth/login", 200,
               data={"username": f"_dr_{ts}", "password": "123"})
DR_TOKEN = dr_body['data']['token'] if dr_body and dr_body.get('code') == 200 else None

ph_body = test("Login pharmacist", "POST", "/auth/login", 200,
               data={"username": f"_ph_{ts}", "password": "123"})
PH_TOKEN = ph_body['data']['token'] if ph_body and ph_body.get('code') == 200 else None

rt_body = test("Login root", "POST", "/auth/login", 200,
               data={"username": f"_rt_{ts}", "password": "123"})
RT_TOKEN = rt_body['data']['token'] if rt_body and rt_body.get('code') == 200 else None

# ========== Step 2: Auth Tests ==========
print("\nStep 2: Auth endpoints...")
test("Login wrong password", "POST", "/auth/login", 401,
     data={"username": "admin", "password": "wrong"})
test("Login empty fields", "POST", "/auth/login", 400,
     data={"username": "", "password": ""})
test("Auto-login empty machineId", "POST", "/auth/auto-login", 400,
     data={"machineId": ""})
test("Logout", "POST", "/auth/logout", token=ADMIN_TOKEN)

# Re-login admin after logout
body = test("Re-login admin", "POST", "/auth/login", 200,
            data={"username": "admin", "password": "admin123"})
ADMIN_TOKEN = body['data']['token'] if body and body.get('code') == 200 else None

# ========== Step 3: User Management (ADMIN) ==========
print("\nStep 3: User management (ADMIN)...")
test("GET /users", "GET", "/users", 200, token=ADMIN_TOKEN, params={"page": 1, "size": 10})
test("PATCH /users/{id}/status", "PATCH", "/users/2/status", 200, token=ADMIN_TOKEN, params={"status": 1})

# RBAC: non-admin cannot access users
if DR_TOKEN:
    test("RBAC: doctor GET /users → 403", "GET", "/users", 403, token=DR_TOKEN)

# ========== Step 4: Drugs (DOCTOR/PHARMACIST/ROOT) ==========
print("\nStep 4: Drug endpoints (ROOT)...")
test("GET /drugs (paginated)", "GET", "/drugs", 200, token=RT_TOKEN, params={"page": 1, "size": 10})
test("POST /drugs (add)", "POST", "/drugs", 200, token=RT_TOKEN,
     data={"name": "_test_drug", "spec": "10mg", "unit": "box", "price": 25.5, "manufacturer": "Test Mfg"})
test("POST /drugs/migrate-batches", "POST", "/drugs/migrate-batches", 200, token=RT_TOKEN)

# ========== Step 5: Diagnosis Types (DOCTOR for write, DOCTOR/PHARMACIST for read) ==========
print("\nStep 5: Diagnosis Types...")
test("GET /diagnosis-types (paginated)", "GET", "/diagnosis-types", 200, token=RT_TOKEN,
     params={"page": 1, "size": 50})
test("POST /diagnosis-types (add)", "POST", "/diagnosis-types", 200, token=RT_TOKEN,
     data={"name": f"_diag_{ts}"})
test("PUT /diagnosis-types/1", "PUT", "/diagnosis-types/1", 200, token=RT_TOKEN,
     data={"name": "Test Updated"})
# Restore original name
test("PUT /diagnosis-types/1 (restore)", "PUT", "/diagnosis-types/1", 200, token=RT_TOKEN,
     data={"name": "上呼吸道感染"})

# ========== Step 6: Visits (DOCTOR submit, PHARMACIST dispense/return) ==========
print("\nStep 6: Visits...")
test("GET /visits", "GET", "/visits", 200, token=RT_TOKEN, params={"page": 1, "size": 10})
test("GET /visits/notification-counts", "GET", "/visits/notification-counts", 200, token=RT_TOKEN)

# Submit prescription (DOCTOR)
submit_body = {
    "patientName": "Test Patient",
    "gender": "男",
    "age": 30,
    "diagnosisId": 1,
    "department": "本厂",
    "visitDate": "2026-06-02",
    "drugs": [{"drugId": 1, "quantity": 1}]
}
test("POST /visits (submit prescription)", "POST", "/visits", 200, token=RT_TOKEN, data=submit_body)

# ========== Step 7: Purchases (DOCTOR/PHARMACIST) ==========
print("\nStep 7: Purchases...")
test("GET /purchases?month=2026-06", "GET", "/purchases", 200, token=RT_TOKEN, params={"month": "2026-06"})

# ========== Step 8: Purchase Plans ==========
print("\nStep 8: Purchase Plans...")
test("POST /purchase-plans/generate", "POST", "/purchase-plans/generate", 200, token=RT_TOKEN,
     params={"month": "2026-06"})
test("GET /drug/{id}/manufacturers", "GET", "/purchase-plans/drug/1/manufacturers", 200, token=RT_TOKEN)

# ========== Step 9: Stats ==========
print("\nStep 9: Stats...")
test("GET /stats/drugs", "GET", "/stats/drugs", 200, token=RT_TOKEN, params={"month": "2026-06"})
test("GET /stats/operations", "GET", "/stats/operations", 200, token=RT_TOKEN, params={"month": "2026-06"})
test("GET /stats/monthly-summary", "GET", "/stats/monthly-summary", 200, token=RT_TOKEN, params={"month": "2026-06"})
test("GET /stats/yearly-summary", "GET", "/stats/yearly-summary", 200, token=RT_TOKEN, params={"year": "2026"})
test("GET /stats/purchase-plan", "GET", "/stats/purchase-plan", 200, token=RT_TOKEN, params={"month": "2026-06"})
test("GET /stats/inventory-check", "GET", "/stats/inventory-check", 200, token=RT_TOKEN, params={"month": "2026-06"})

# ========== Step 10: Operation Logs (ADMIN) ==========
print("\nStep 10: Operation Logs...")
test("GET /operation-logs", "GET", "/operation-logs", 200, token=ADMIN_TOKEN, params={"page": 1, "size": 10})

# ========== Step 11: Inventory Checks (PHARMACIST) ==========
print("\nStep 11: Inventory Checks...")
test("GET /inventory-checks/pending", "GET", "/inventory-checks/pending", 200, token=RT_TOKEN)
test("POST /inventory-checks/generate", "POST", "/inventory-checks/generate", 200, token=RT_TOKEN,
     params={"month": "2026-06"})

# ========== Summary ==========
print("\n" + "=" * 70)
passed = sum(1 for s, _, _ in RESULTS if s == "PASS")
failed = sum(1 for s, _, _ in RESULTS if s == "FAIL")
print(f"Total: {len(RESULTS)} | PASS: {passed} | FAIL: {failed}")
print("=" * 70)
for s, n, d in RESULTS:
    print(f"  [{s}] {n}: {d}")

if failed > 0:
    print(f"\n{failed} FAILURES")
    sys.exit(1)
else:
    print("\nALL {0} TESTS PASSED".format(passed))
