from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
from utils.api_client import api_client
from ui.style_constants import *
from ui.components import ModernButton, SidebarButton, ModernLabel, BadgedSidebarButton, ToastNotification

class MainWindow(QMainWindow):
    stock_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._prev_pending = 0
        self._prev_returned = 0
        self._badged_buttons = {}
        self.initUI()
        self._start_notification_poller()

    def initUI(self):
        self.setWindowTitle(f'药品出入库系统 - {api_client.user_role}')
        self.resize(1280, 800)

        main_widget = QWidget()
        main_widget.setStyleSheet(f"background-color: {WINDOW_BG};")
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo_container = QWidget()
        logo_container.setFixedHeight(80)
        logo_container.setStyleSheet(f"background-color: {SIDEBAR_BG}; border-bottom: 1px solid {SIDEBAR_HOVER};")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_title = QLabel("药品出入库管理系统")
        app_title.setStyleSheet(f"color: {WHITE}; font-size: {FONT_SIZE_XL}; font-weight: bold;")
        logo_layout.addWidget(app_title)
        sidebar_layout.addWidget(logo_container)

        user_container = QWidget()
        user_container.setFixedHeight(100)
        user_container.setStyleSheet("background-color: transparent;")
        user_layout = QVBoxLayout(user_container)
        user_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_label = QLabel(api_client.user_role)
        role_label.setStyleSheet(f"""
            color: {WHITE};
            font-size: {FONT_SIZE_LG};
            background-color: {SIDEBAR_BG};
            padding: 4px 12px;
            border-radius: 12px;
        """)
        user_layout.addWidget(role_label)
        sidebar_layout.addWidget(user_container)

        menu_container = QWidget()
        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(0, 10, 0, 10)
        menu_layout.setSpacing(5)
        self.menu_buttons = []
        self.create_menu(menu_layout)
        sidebar_layout.addWidget(menu_container)

        sidebar_layout.addStretch()
        logout_container = QWidget()
        logout_container.setContentsMargins(20, 20, 20, 20)
        logout_layout = QVBoxLayout(logout_container)
        logout_btn = ModernButton("退出登录", variant="danger")
        logout_btn.clicked.connect(self.logout)
        logout_layout.addWidget(logout_btn)
        sidebar_layout.addWidget(logout_container)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(SPACING_XL_INT, SPACING_XL_INT, SPACING_XL_INT, SPACING_XL_INT)
        self.header_label = ModernLabel("首页", size=FONT_SIZE_2XL, weight=FONT_WEIGHT_BOLD, color=GRAY_800)
        content_layout.addWidget(self.header_label)
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_container)

        self.load_views()

    def create_menu(self, layout):
        role = api_client.user_role
        # (text, index, is_notifiable) — is_notifiable 表示该按钮需要徽标
        menus = []

        if role == 'ADMIN':
            menus = [("👤 医生管理", 0, False), ("📋 操作日志", 1, False)]
        elif role == 'DOCTOR':
            menus = [("📝 就诊登记", 0, False), ("📋 就诊记录", 1, True), ("💊 药品查询", 2, False), ("📊 统计报表", 3, False)]
        elif role == 'PHARMACIST':
            menus = [("📦 待发药", 0, True), ("📋 发药记录", 1, False), ("🔍 库存盘点", 2, False),
                     ("💊 药品管理", 3, False), ("📥 药品购进", 4, False), ("📊 统计报表", 5, False)]
        elif role == 'ROOT':
            menus = [("📝 就诊登记", 0, False), ("📋 就诊记录", 1, True), ("📦 待发药", 2, True),
                     ("📋 发药记录", 3, False), ("🔍 库存盘点", 4, False), ("💊 药品管理", 5, False),
                     ("📥 药品购进", 6, False), ("📊 统计报表", 7, False)]

        for text, index, notifiable in menus:
            if notifiable:
                btn = BadgedSidebarButton(text)
                # 用纯文字（去 emoji 前缀）作徽标查找 key，因为通知代码不知道 emoji
                plain = text.split(" ", 1)[-1] if " " in text else text
                self._badged_buttons[plain] = btn
            else:
                btn = SidebarButton(text)
            btn.clicked.connect(lambda checked, idx=index, t=text: self.switch_view(idx, t))
            self.menu_buttons.append(btn)
            layout.addWidget(btn)

    def load_views(self):
        role = api_client.user_role
        if role == 'ADMIN':
            from ui.admin_views import UserManageView, LogView
            self.content_stack.addWidget(UserManageView())
            self.content_stack.addWidget(LogView())
        elif role == 'DOCTOR':
            from ui.doctor_views import VisitCreateView, VisitHistoryView, DrugQueryView
            from ui.pharmacist_views import StatsView
            self.content_stack.addWidget(VisitCreateView())
            self.content_stack.addWidget(VisitHistoryView())
            self.content_stack.addWidget(DrugQueryView())
            self.content_stack.addWidget(StatsView())
        elif role == 'PHARMACIST':
            from ui.pharmacist_views import DispenseView, DispenseHistoryView, InventoryView, DrugManageView, StatsView, PurchaseView
            self.content_stack.addWidget(DispenseView())
            self.content_stack.addWidget(DispenseHistoryView())
            self.content_stack.addWidget(InventoryView())
            self.content_stack.addWidget(DrugManageView())
            self.content_stack.addWidget(PurchaseView())
            self.content_stack.addWidget(StatsView())
        elif role == 'ROOT':
            from ui.doctor_views import VisitCreateView, VisitHistoryView
            from ui.pharmacist_views import DispenseView, DispenseHistoryView, InventoryView, DrugManageView, StatsView, PurchaseView
            self.content_stack.addWidget(VisitCreateView())
            self.content_stack.addWidget(VisitHistoryView())
            self.content_stack.addWidget(DispenseView())
            self.content_stack.addWidget(DispenseHistoryView())
            self.content_stack.addWidget(InventoryView())
            self.content_stack.addWidget(DrugManageView())
            self.content_stack.addWidget(PurchaseView())
            self.content_stack.addWidget(StatsView())

        if self.menu_buttons:
            self.menu_buttons[0].click()

    # ==================== 通知系统 ====================

    def _start_notification_poller(self):
        self._notify_timer = QTimer(self)
        self._notify_timer.timeout.connect(self._check_notifications)
        self._notify_timer.start(5000)  # 每5秒轮询

    def _check_notifications(self):
        role = api_client.user_role
        try:
            res = api_client.get("/visits/notification-counts")
            if res.status_code != 200:
                return
            data = res.json()
            if data.get('code') != 200:
                return
            counts = data.get('data', {})
            pending = counts.get('pendingCount', 0)
            returned = counts.get('returnedCount', 0)

            # 药师/ROOT: 待发药徽标（始终更新，处理完自动清零）
            if role in ('PHARMACIST', 'ROOT'):
                self._update_badge("待发药", pending)
                if pending > self._prev_pending:
                    diff = pending - self._prev_pending
                    self._show_toast(f"有 {diff} 条新处方待处理", lambda: self.switch_view(
                        self._find_menu_index("待发药"), "待发药"))

            # 医师/ROOT: 就诊记录徽标（始终更新，处理完自动清零）
            if role in ('DOCTOR', 'ROOT'):
                self._update_badge("就诊记录", returned)
                if returned > self._prev_returned:
                    diff = returned - self._prev_returned
                    self._show_toast(f"有 {diff} 条处方状态已更新", lambda: self.switch_view(
                        self._find_menu_index("就诊记录"), "就诊记录"))

            self._prev_pending = pending
            self._prev_returned = returned

        except Exception:
            pass

    def _update_badge(self, menu_text, count):
        btn = self._badged_buttons.get(menu_text)
        if btn:
            btn.set_badge(count)

    def _show_toast(self, message, on_click=None):
        toast = ToastNotification(self, message)
        toast.move(self.width() - toast.width() - 30, self.height() - toast.height() - 50)
        if on_click:
            toast.clicked.connect(on_click)
        toast.show()

    def _find_menu_index(self, text):
        for i, btn in enumerate(self.menu_buttons):
            if hasattr(btn, '_base_text') and text in btn._base_text:
                return i
            if text in btn.text():
                return i
        return 0

    # ==================== 视图切换 ====================

    def switch_view(self, index, title):
        self.content_stack.setCurrentIndex(index)
        self.header_label.setText(title)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 重绘时需要调整已显示 toast 的位置（简单处理：不追踪已存在的 toast）

    def logout(self):
        try:
            import uuid
            node = uuid.getnode()
            machine_id = str(node)
        except Exception:
            machine_id = None
        if self._notify_timer:
            self._notify_timer.stop()
        api_client.logout(machine_id)
        self.close()
