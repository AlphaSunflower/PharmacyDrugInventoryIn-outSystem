from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from utils.api_client import api_client
from ui.style_constants import *
from ui.components import ModernButton, SidebarButton, ModernLabel

class MainWindow(QMainWindow):
    stock_changed = pyqtSignal()  # 发药/购进后通知各视图刷新库存

    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(f'药品出入库系统 - {api_client.user_role}')
        self.resize(1280, 800)
        
        # 主布局
        main_widget = QWidget()
        main_widget.setStyleSheet(f"background-color: {WINDOW_BG};")
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 侧边栏
        sidebar = QFrame()
        sidebar.setFixedWidth(240) # 加宽侧边栏
        sidebar.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/标题区域
        logo_container = QWidget()
        logo_container.setFixedHeight(80)
        logo_container.setStyleSheet(f"background-color: {SIDEBAR_BG}; border-bottom: 1px solid {SIDEBAR_HOVER};")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        app_title = QLabel("药品出入库管理系统")
        app_title.setStyleSheet(f"color: {WHITE}; font-size: {FONT_SIZE_XL}; font-weight: bold;")
        logo_layout.addWidget(app_title)
        
        sidebar_layout.addWidget(logo_container)
        
        # 用户信息区域
        user_container = QWidget()
        user_container.setFixedHeight(100)
        user_container.setStyleSheet("background-color: transparent;")
        user_layout = QVBoxLayout(user_container)
        user_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 这里可以用图标代替文字
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
        
        # 菜单按钮容器
        menu_container = QWidget()
        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(0, 10, 0, 10)
        menu_layout.setSpacing(5)
        
        self.menu_buttons = []
        self.create_menu(menu_layout)
        
        sidebar_layout.addWidget(menu_container)
        
        # 底部区域（退出按钮）
        sidebar_layout.addStretch()
        
        logout_container = QWidget()
        logout_container.setContentsMargins(20, 20, 20, 20)
        logout_layout = QVBoxLayout(logout_container)
        
        logout_btn = ModernButton("退出登录", variant="danger")
        logout_btn.clicked.connect(self.logout)
        logout_layout.addWidget(logout_btn)
        
        sidebar_layout.addWidget(logout_container)
        
        # 内容区域
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(SPACING_XL_INT, SPACING_XL_INT, SPACING_XL_INT, SPACING_XL_INT)
        
        # 顶部面包屑/标题栏
        self.header_label = ModernLabel("首页", size=FONT_SIZE_2XL, weight=FONT_WEIGHT_BOLD, color=GRAY_800)
        content_layout.addWidget(self.header_label)
        
        # 页面堆栈
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_container)
        
        self.load_views()

    def create_menu(self, layout):
        role = api_client.user_role
        menus = []
        
        if role == 'ADMIN':
            menus = [
                ("医生管理", 0),
                ("操作日志", 1)
            ]
        elif role == 'DOCTOR':
            menus = [
                ("就诊登记", 0),
                ("就诊记录", 1),
                ("药品查询", 2),
                ("统计报表", 3)
            ]
        elif role == 'PHARMACIST':
            menus = [
                ("待发药", 0),
                ("发药记录", 1),
                ("库存盘点", 2),
                ("药品管理", 3),
                ("药品购进", 4),
                ("统计报表", 5)
            ]
        elif role == 'ROOT':
            menus = [
                ("就诊登记", 0),
                ("就诊记录", 1),
                ("待发药", 2),
                ("发药记录", 3),
                ("库存盘点", 4),
                ("药品管理", 5),
                ("药品购进", 6),
                ("统计报表", 7)
            ]
            
        for text, index in menus:
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
            # 复用药师的 StatsView
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
            
            # 按菜单顺序添加
            self.content_stack.addWidget(VisitCreateView())
            self.content_stack.addWidget(VisitHistoryView())
            self.content_stack.addWidget(DispenseView())
            self.content_stack.addWidget(DispenseHistoryView())
            self.content_stack.addWidget(InventoryView())
            self.content_stack.addWidget(DrugManageView())
            self.content_stack.addWidget(PurchaseView())
            self.content_stack.addWidget(StatsView())
            
        # 默认显示第一个页面
        if self.menu_buttons:
            self.menu_buttons[0].click()

    def switch_view(self, index, title):
        self.content_stack.setCurrentIndex(index)
        self.header_label.setText(title)
        # 更新按钮状态
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)

    def logout(self):
        # 退出时传递机器码，用于判断是否需要解绑自动登录
        try:
            import uuid
            node = uuid.getnode()
            machine_id = str(node)
        except:
            machine_id = None
            
        api_client.logout(machine_id)
        self.close()
