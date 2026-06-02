"""Verify stats bug fixes — uses ROOT account directly"""
import requests, json

BASE = "http://localhost:8080/api/v1"

# Login as ROOT (has both doctor and pharmacist privileges)
r = requests.post(f"{BASE}/auth/login", json={"username": "root", "password": "root123"})
assert r.status_code == 200 and r.json()["code"] == 200, f"Login failed: {r.json()}"
TOKEN = r.json()["data"]["token"]
AUTH = {"Authorization": f"Bearer {TOKEN}"}
print(f"Logged in as ROOT (token={TOKEN[:20]}...)")

# Verify password is NOT in login response
user_data = r.json()["data"]["user"]
assert "password" not in user_data, "BUG: password visible in login response!"
print("H1 verified: password hidden from API response")

passed = 0
failed = 0

def test(name, resp, checks):
    global passed, failed
    try:
        data = resp.json() if resp.text else {}
        failures = [desc for desc, fn in checks if not fn(data)]
        if not failures:
            passed += 1
            print(f"  PASS [{name}]")
        else:
            failed += 1
            print(f"  FAIL [{name}]")
            for f_desc in failures:
                print(f"    -> {f_desc}")
            print(f"    body: {json.dumps(data, ensure_ascii=False)[:200]}")
    except Exception as e:
        failed += 1
        print(f"  FAIL [{name}] {e}")

# BUG1: endAmount exists even when drug not in inventory
r = requests.get(f"{BASE}/stats/drugs", params={"month": "2026-06"}, headers=AUTH)
test("BUG1-endAmount", r, [
    ("code=200", lambda d: d.get("code") == 200),
    ("has list", lambda d: "list" in d.get("data", {})),
    ("all endAmount not None", lambda d: all(
        item.get("endAmount") is not None
        for item in d.get("data", {}).get("list", [])
    )),
])

# BUG2: No crash with valid data (tests NPE fix)
r = requests.get(f"{BASE}/stats/drugs", params={"month": "2026-01"}, headers=AUTH)
test("BUG2-noNPE", r, [
    ("code=200", lambda d: d.get("code") == 200),
])

# BUG3+BUG5: Yearly summary has isYearEndStockMissing
r = requests.get(f"{BASE}/stats/yearly-summary", params={"year": "2026"}, headers=AUTH)
test("BUG3-yearEndMissing", r, [
    ("code=200", lambda d: d.get("code") == 200),
    ("has isYearEndStockMissing", lambda d: "isYearEndStockMissing" in d.get("data", {})),
    ("has missingInventoryMonths", lambda d: "missingInventoryMonths" in d.get("data", {})),
])

# BUG5: Monthly summary has all new fields
r = requests.get(f"{BASE}/stats/monthly-summary", params={"month": "2026-06"}, headers=AUTH)
test("BUG5-monthlyFields", r, [
    ("code=200", lambda d: d.get("code") == 200),
    ("has missingInventoryMonths", lambda d: "missingInventoryMonths" in d.get("data", {})),
    ("has isLastYearStockMissing", lambda d: "isLastYearStockMissing" in d.get("data", {})),
    ("has isYearEndStockMissing", lambda d: "isYearEndStockMissing" in d.get("data", {})),
])

# BUG6: Verify drug stats can handle edge cases
r = requests.get(f"{BASE}/stats/operations", params={"month": "2026-06"}, headers=AUTH)
test("Stats-operations", r, [
    ("code=200", lambda d: d.get("code") == 200),
    ("has dailyStats", lambda d: "dailyStats" in d.get("data", {})),
    ("has summary", lambda d: "summary" in d.get("data", {})),
])

# Excel export tests
r = requests.get(f"{BASE}/stats/monthly-summary/export", params={"month": "2026-06"}, headers=AUTH)
if r.status_code == 200:
    passed += 1; print(f"  PASS [Excel-monthly] HTTP 200 ({len(r.content)} bytes)")
else:
    failed += 1; print(f"  FAIL [Excel-monthly] HTTP {r.status_code}")

r = requests.get(f"{BASE}/stats/yearly-summary/export", params={"year": "2026"}, headers=AUTH)
if r.status_code == 200:
    passed += 1; print(f"  PASS [Excel-yearly] HTTP 200 ({len(r.content)} bytes)")
else:
    failed += 1; print(f"  FAIL [Excel-yearly] HTTP {r.status_code}")

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
assert failed == 0, f"{failed} test(s) failed!"
print("ALL TESTS PASSED")
