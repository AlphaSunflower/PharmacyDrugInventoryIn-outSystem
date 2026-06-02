import os
import requests

class APIClient:
    BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080/api/v1")

    TIMEOUT = (5, 15)  # (connect, read) timeout in seconds

    def __init__(self):
        self.token = None
        self.user_role = None
        self.user_id = None
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def login(self, username, password, machine_id=None, auto_login=False):
        try:
            payload = {"username": username, "password": password}
            if machine_id:
                payload["machineId"] = machine_id
                payload["autoLogin"] = auto_login

            response = self._session.post(
                f"{self.BASE_URL}/auth/login", json=payload, timeout=self.TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 200:
                    self.token = data["data"]["token"]
                    self.user_role = data["data"]["user"]["role"]
                    self.user_id = data["data"]["user"]["id"]
                    return True, "登录成功"
                return False, data["message"]
            return False, f"HTTP {response.status_code}"
        except requests.ConnectionError:
            return False, "无法连接服务器，请检查网络"
        except requests.Timeout:
            return False, "请求超时，请重试"
        except Exception as e:
            return False, str(e)

    def auto_login(self, machine_id):
        try:
            response = self._session.post(
                f"{self.BASE_URL}/auth/auto-login",
                json={"machineId": machine_id},
                timeout=self.TIMEOUT,
            )
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 200:
                    self.token = data["data"]["token"]
                    self.user_role = data["data"]["user"]["role"]
                    self.user_id = data["data"]["user"]["id"]
                    return True, "自动登录成功"
            return False, "自动登录失败"
        except requests.ConnectionError:
            return False, "无法连接服务器"
        except requests.Timeout:
            return False, "请求超时"
        except Exception:
            return False, "网络错误"

    def logout(self, machine_id=None):
        try:
            data = {"machineId": machine_id} if machine_id else {}
            self.post("/auth/logout", data=data)
        except Exception:
            pass
        finally:
            self.token = None
            self.user_role = None
            self.user_id = None
            return True

    def _get_headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, endpoint, params=None):
        return self._session.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers(),
            params=params,
            timeout=self.TIMEOUT,
        )

    def post(self, endpoint, data=None, params=None):
        return self._session.post(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers(),
            json=data,
            params=params,
            timeout=self.TIMEOUT,
        )

    def put(self, endpoint, data=None, params=None):
        return self._session.put(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers(),
            json=data,
            params=params,
            timeout=self.TIMEOUT,
        )

    def patch(self, endpoint, data=None, params=None):
        return self._session.patch(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers(),
            json=data,
            params=params,
            timeout=self.TIMEOUT,
        )

    def delete(self, endpoint, params=None):
        return self._session.delete(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers(),
            params=params,
            timeout=self.TIMEOUT,
        )

    # ==================== 采购计划 ====================

    def generate_purchase_plan(self, month):
        return self.post("/purchase-plans/generate", params={"month": month})

    def get_purchase_plan_details(self, plan_id):
        return self.get(f"/purchase-plans/{plan_id}/details")

    def update_purchase_plan_detail(self, detail_id, planned_quantity=None, manufacturer=None):
        data = {}
        if planned_quantity is not None:
            data["plannedQuantity"] = planned_quantity
        if manufacturer is not None:
            data["manufacturer"] = manufacturer
        return self.put(f"/purchase-plans/details/{detail_id}", data=data)

    def complete_purchase_plan(self, plan_id):
        return self.post(f"/purchase-plans/{plan_id}/complete")

    def reopen_purchase_plan(self, plan_id):
        return self.post(f"/purchase-plans/{plan_id}/reopen")

    def delete_purchase_plan(self, plan_id):
        return self.delete(f"/purchase-plans/{plan_id}")

    def get_drug_manufacturers(self, drug_id):
        return self.get(f"/purchase-plans/drug/{drug_id}/manufacturers")


api_client = APIClient()
