import sys
import uuid
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt
from utils.api_client import api_client
from ui.components import ModernButton, ModernInput, ModernLabel, ModernCard, ModernMessageBox
from ui.style_constants import *

def get_machine_id():
    """获取简单的机器码"""
    try:
        # 使用 MAC 地址作为机器码的基础
        node = uuid.getnode()
        return str(node)
    except:
        return None

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('药品出入库系统 - 登录')
        self.resize(1024, 768)
        self.setStyleSheet(f"background-color: {GRAY_100};")
        
        # 主布局，用于居中显示卡片
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 登录卡片
        card = ModernCard()
        card.setFixedSize(420, 520)
        card.setStyleSheet(f"""
            ModernCard {{
                background-color: {WHITE};
                border-radius: {RADIUS_LG};
                border: 1px solid {GRAY_200};
            }}
        """)
        
        # 卡片内部布局
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(10)
        title_layout.setContentsMargins(0, 20, 0, 30)
        
        title = ModernLabel('欢迎登录', size=FONT_SIZE_2XL, weight=FONT_WEIGHT_BOLD, color=PRIMARY_COLOR)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)
        
        subtitle = ModernLabel('药品出入库管理系统', size=FONT_SIZE_SM, color=GRAY_500)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle)
        
        card.add_layout(title_layout)
        
        # 表单区域
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        # 用户名
        self.username_input = ModernInput(placeholder='用户名')
        self.username_input.setMinimumHeight(45)
        form_layout.addWidget(self.username_input)
        
        # 密码
        self.password_input = ModernInput(placeholder='密码')
        self.password_input.setMinimumHeight(45)
        self.password_input.setEchoMode(ModernInput.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login) # 回车登录
        form_layout.addWidget(self.password_input)
        
        card.add_layout(form_layout)
        
        # 自动登录选项
        cb_layout = QHBoxLayout()
        cb_layout.setContentsMargins(5, 10, 5, 10)
        self.auto_login_cb = QCheckBox("下次自动登录（绑定本机）")
        self.auto_login_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_login_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {GRAY_600};
                font-size: {FONT_SIZE_SM};
                font-family: "{FONT_FAMILY}";
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_SM};
                background-color: {WHITE};
            }}
            QCheckBox::indicator:hover {{
                border-color: {PRIMARY_COLOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {PRIMARY_COLOR};
                border-color: {PRIMARY_COLOR};
                /* 这里可以使用图片，或者简单的颜色填充 */
            }}
        """)
        cb_layout.addWidget(self.auto_login_cb)
        card.add_layout(cb_layout)
        
        # 登录按钮
        login_btn = ModernButton('立即登录', variant="primary")
        login_btn.setMinimumHeight(45)
        login_btn.setStyleSheet(login_btn.styleSheet() + f"font-size: {FONT_SIZE_BASE};")
        login_btn.clicked.connect(self.handle_login)
        card.add_widget(login_btn)
        
        # 底部版权
        footer_layout = QVBoxLayout()
        footer_layout.addStretch()
        copyright_label = ModernLabel('© 2026 AlphaSunflower', size=FONT_SIZE_XS, color=GRAY_400)
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(copyright_label)
        card.add_layout(footer_layout)
        
        main_layout.addWidget(card)
        
    def handle_login(self):
        from ui.main_window import MainWindow
        
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            ModernMessageBox.warning(self, '提示', '请输入用户名和密码')
            return
        
        machine_id = get_machine_id()
        auto_login = self.auto_login_cb.isChecked()
        
        # 显示加载状态 (简单模拟)
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        QApplication.processEvents()
        
        try:
            success, message = api_client.login(username, password, machine_id, auto_login)
            if success:
                self.main_window = MainWindow()
                self.main_window.show()
                self.close()
            else:
                ModernMessageBox.critical(self, '登录失败', message)
        finally:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.username_input.setEnabled(True)
            self.password_input.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置全局字体 (先设 size 再设 family，避免 pointSize 读取到 -1)
    font = app.font()
    font.setPixelSize(14)  # 用像素大小代替 pointSize，避免 CSS→QFont 转换时出现 -1
    font.setFamily(FONT_FAMILY)
    app.setFont(font)
    
    # 尝试自动登录
    machine_id = get_machine_id()
    if machine_id:
        success, msg = api_client.auto_login(machine_id)
        if success:
            from ui.main_window import MainWindow
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
