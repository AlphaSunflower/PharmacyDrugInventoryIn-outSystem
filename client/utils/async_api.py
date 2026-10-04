"""
async_api.py — 基于 QThread 的异步 API 调用基础设施

使用方式:
    from utils.async_api import run_async

    def load_data(self):
        def on_success(data):
            self.drugs = data['records']
            self.refresh_table()

        def on_error(msg):
            ModernMessageBox.critical(self, "错误", f"加载失败: {msg}")

        run_async(self, 'get', '/drugs', params={...},
                  on_success=on_success, on_error=on_error)

原理:
    所有 API 调用在后台 QThread 中执行，不阻塞 Qt 主事件循环。
    完成后通过 pyqtSignal 安全地回到主线程更新 UI。
"""
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from utils.api_client import api_client


class ApiWorker(QObject):
    """在后台线程执行单次 API 请求，通过信号通知调用方"""

    finished = pyqtSignal(object)  # emit (success: bool, data: dict | None, error_msg: str)

    def __init__(self, method: str, endpoint: str, data=None, params=None):
        super().__init__()
        self.method = method
        self.endpoint = endpoint
        self.data = data
        self.params = params

    def run(self):
        """在后台线程中执行（由 QThread.started 触发）"""
        try:
            callable_method = getattr(api_client, self.method)
            kwargs = {}
            if self.data is not None:
                kwargs["data"] = self.data
            if self.params is not None:
                kwargs["params"] = self.params

            res = callable_method(self.endpoint, **kwargs)

            if res.status_code == 200:
                body = api_client.safe_json(res)
                if body is None:
                    self.finished.emit((False, None, "服务器返回了无效响应"))
                    return
                if body.get("code") == 200:
                    self.finished.emit((True, body.get("data"), ""))
                else:
                    self.finished.emit((False, None, body.get("message", "操作失败")))
            else:
                self.finished.emit((False, None, f"HTTP {res.status_code}"))
        except Exception as e:
            self.finished.emit((False, None, str(e)))


def run_async(parent, method, endpoint, data=None, params=None,
              on_success=None, on_error=None, on_finished=None):
    """
    创建一个后台线程运行 API 调用。

    Args:
        parent: QWidget / QObject — 管理线程生命周期（parent 销毁时自动清理线程）
        method:  'get' | 'post' | 'put' | 'delete' | 'patch'
        endpoint: API 路径，如 '/drugs'、'/drugs/123'
        data:     request body dict（POST/PUT 用）
        params:   URL query params dict（GET 用）
        on_success:  callable(data) — 成功回调（在主线程执行）
        on_error:    callable(error_msg) — 失败回调（在主线程执行）
        on_finished: callable() — 不论成败都会调用

    Returns:
        QThread 实例，调用方可以保存引用以管理生命周期
    """
    thread = QThread(parent)
    worker = ApiWorker(method, endpoint, data, params)
    worker.moveToThread(thread)

    def handle_result(result):
        success, data, error_msg = result
        if success:
            if on_success:
                on_success(data)
        else:
            if on_error:
                on_error(error_msg)
        if on_finished:
            on_finished()
        thread.quit()

    worker.finished.connect(handle_result)
    thread.started.connect(worker.run)
    # Qt 6: QThread.finished 自动 deleteLater worker + thread
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
