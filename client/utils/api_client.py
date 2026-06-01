import os
import requests

class APIClient:
    BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080/api/v1")

    def __init__(self):
        self.token = None
        self.user_role = None
        self.user_id = None
        
    def login(self, username, password, machine_id=None, auto_login=False):
        try:
            payload = {
                "username": username,
                "password": password
            }
            if machine_id:
                payload["machineId"] = machine_id
                payload["autoLogin"] = auto_login
                
            response = requests.post(f"{self.BASE_URL}/auth/login", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    self.token = data['data']['token']
                    self.user_role = data['data']['user']['role']
                    self.user_id = data['data']['user']['id']
                    return True, "登录成功"
                else:
                    return False, data['message']
            return False, f"HTTP Error: {response.status_code}"
        except Exception as e:
            return False, str(e)

    def auto_login(self, machine_id):
        try:
            response = requests.post(f"{self.BASE_URL}/auth/auto-login", json={"machineId": machine_id})
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    self.token = data['data']['token']
                    self.user_role = data['data']['user']['role']
                    self.user_id = data['data']['user']['id']
                    return True, "自动登录成功"
            return False, "自动登录失败"
        except Exception:
            return False, "网络错误"

    def logout(self, machine_id=None):
        try:
            data = {"machineId": machine_id} if machine_id else {}
            # 注意：logout 需要 token，所以使用 self.post
            self.post("/auth/logout", data=data)
            self.token = None
            self.user_role = None
            self.user_id = None
            return True
        except:
            return False

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # 封装通用的 GET/POST/PUT 请求
    def get(self, endpoint, params=None):
        return requests.get(f"{self.BASE_URL}{endpoint}", headers=self.get_headers(), params=params)

    def post(self, endpoint, data=None, params=None):
        return requests.post(f"{self.BASE_URL}{endpoint}", headers=self.get_headers(), json=data, params=params)

    def put(self, endpoint, data=None, params=None):
        return requests.put(f"{self.BASE_URL}{endpoint}", headers=self.get_headers(), json=data, params=params)

    def patch(self, endpoint, data=None, params=None):
        return requests.patch(f"{self.BASE_URL}{endpoint}", headers=self.get_headers(), json=data, params=params)

    def delete(self, endpoint, params=None):
        return requests.delete(f"{self.BASE_URL}{endpoint}", headers=self.get_headers(), params=params)

api_client = APIClient()
