from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QHBoxLayout, QMessageBox, 
                             QDialog, QFormLayout, QLineEdit, QComboBox, QHeaderView, QFrame, QTextEdit,
                             QGridLayout)
import json
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils.api_client import api_client
from ui.style_constants import *
from ui.components import ModernButton, ModernInput, ModernLabel, ModernCard, ModernMessageBox, ModernTable

class LogDetailsDialog(QDialog):
    def __init__(self, log, parent=None):
        super().__init__(parent)
        self.log = log
        self.setWindowTitle("日志详情")
        self.setFixedSize(600, 500)
        self.setStyleSheet(f"background-color: {WHITE};")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        layout.addWidget(ModernLabel("操作日志详情", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))

        # 基本信息
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        form_layout.addRow(ModernLabel("日志ID:"), ModernLabel(str(self.log['id'])))
        form_layout.addRow(ModernLabel("操作人:"), ModernLabel(f"{self.log.get('username', '-')} ({self.log.get('role', '-')})"))
        form_layout.addRow(ModernLabel("操作内容:"), ModernLabel(self.log['action']))
        form_layout.addRow(ModernLabel("操作时间:"), ModernLabel(str(self.log['createdAt'])))
        
        layout.addLayout(form_layout)

        # 操作数据详情
        layout.addWidget(ModernLabel("操作数据:", weight=FONT_WEIGHT_BOLD))
        
        data_text = QTextEdit()
        data_text.setReadOnly(True)
        data_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                padding: 10px;
                background-color: {GRAY_50};
                font-family: Consolas, Monaco, monospace;
            }}
        """)
        
        operate_data = self.log.get('operateData', '')
        if operate_data:
            try:
                # 尝试解析 JSON 并格式化
                parsed_json = json.loads(operate_data)
                formatted_json = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                data_text.setText(formatted_json)
            except (json.JSONDecodeError, TypeError):
                data_text.setText(str(operate_data))
        else:
            data_text.setText("无数据")
            
        layout.addWidget(data_text)

        # 关闭按钮
        close_btn = ModernButton("关闭", variant="secondary")
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)

class UserManageView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_LG_INT)
        
        # 顶部操作栏
        top_card = ModernCard()
        top_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        top_layout = QHBoxLayout()
        
        title_label = ModernLabel("系统用户管理", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        refresh_btn = ModernButton("刷新", variant="outline")
        refresh_btn.clicked.connect(self.load_data)
        top_layout.addWidget(refresh_btn)
        
        add_btn = ModernButton("新增用户", variant="primary")
        add_btn.clicked.connect(self.show_add_dialog)
        top_layout.addWidget(add_btn)
        
        top_card.add_layout(top_layout)
        layout.addWidget(top_card)
        
        # 数据表格区域
        table_card = ModernCard()
        table_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        self.table = ModernTable()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "用户名", "真实姓名", "角色", "状态", "操作"])

        # 表格样式优化
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # 表头样式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID列自适应
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # 状态列自适应
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {GRAY_50};
                color: {GRAY_600};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {GRAY_200};
                font-weight: bold;
            }}
        """)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {WHITE};
                border: none;
                gridline-color: {GRAY_200};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {GRAY_100};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR}10;
                color: {PRIMARY_COLOR};
            }}
            QTableWidget::item:alternate {{
                background-color: {GRAY_50};
            }}
        """)
        
        table_card.add_widget(self.table)
        layout.addWidget(table_card)
        
        self.setLayout(layout)

    def load_data(self):
        res = api_client.get("/users", params={"size": 100})
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.users = data['data']['records']
                self.refresh_table()
            else:
                self.table.setRowCount(0)
        else:
            self.table.setRowCount(0)

    def refresh_table(self):
        self.table.setRowCount(len(self.users))

        for r, u in enumerate(self.users):
            self.table.setItem(r, 0, QTableWidgetItem(str(u['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(u['username']))
            self.table.setItem(r, 2, QTableWidgetItem(u['realName']))
            
            # 角色标签化
            role_item = QTableWidgetItem(u['role'])
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 3, role_item)
            
            # 状态样式化
            status_text = "启用" if u['status'] == 1 else "停用"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(SUCCESS_COLOR) if u['status'] == 1 else QColor(ERROR_COLOR))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 4, status_item)
            
            # 操作按钮
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)
            
            edit_btn = ModernButton("编辑", variant="secondary")
            edit_btn.setFixedSize(70, 38)
            edit_btn.setStyleSheet(edit_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            edit_btn.clicked.connect(lambda _, user=u: self.show_edit_dialog(user))
            
            toggle_text = "停用" if u['status'] == 1 else "启用"
            toggle_variant = "danger" if u['status'] == 1 else "primary" # 启用用primary，停用用danger
            
            toggle_btn = ModernButton(toggle_text, variant=toggle_variant)
            toggle_btn.setFixedSize(70, 38)
            toggle_btn.setStyleSheet(toggle_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            toggle_btn.clicked.connect(lambda _, user=u: self.toggle_status(user))
            
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(toggle_btn)
            btn_layout.addStretch()

            self.table.setCellWidget(r, 5, btn_container)
            row_count = self.table.rowCount()
            for row in range(row_count):
                self.table.setRowHeight(row, 60)

    def show_add_dialog(self):
        self.show_user_dialog("新增用户")

    def show_edit_dialog(self, user):
        self.show_user_dialog("编辑用户", user)

    def show_user_dialog(self, title, user=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 350)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        layout.addWidget(ModernLabel(title, size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        username_edit = ModernInput(user['username'] if user else "")
        if user: username_edit.setReadOnly(True)
        
        realname_edit = ModernInput(user['realName'] if user else "")
        
        role_combo = QComboBox()
        role_combo.addItems(["DOCTOR", "PHARMACIST", "ADMIN", "ROOT"])
        role_combo.setFixedHeight(40)
        role_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 5px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        if user: role_combo.setCurrentText(user['role'])
        
        password_edit = ModernInput()
        password_edit.setPlaceholderText("留空则保持不变" if user else "初始密码")
        
        form_layout.addRow(ModernLabel("用户名:"), username_edit)
        form_layout.addRow(ModernLabel("真实姓名:"), realname_edit)
        form_layout.addRow(ModernLabel("角色:"), role_combo)
        form_layout.addRow(ModernLabel("密码:"), password_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        btn_box = QHBoxLayout()
        save_btn = ModernButton("保存", variant="primary")
        cancel_btn = ModernButton("取消", variant="secondary")
        
        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def save():
            data = {
                "username": username_edit.text(),
                "realName": realname_edit.text(),
                "role": role_combo.currentText()
            }
            if password_edit.text():
                data["password"] = password_edit.text()
            elif not user:
                ModernMessageBox.warning(dialog, "提示", "新增用户必须设置密码")
                return

            if user:
                res = api_client.put(f"/users/{user['id']}", data)
            else:
                res = api_client.post("/users", data)

            resp_data = api_client.safe_json(res) or {}
            if res.status_code == 200 and resp_data.get('code') == 200:
                ModernMessageBox.information(dialog, "成功", "保存成功")
                dialog.accept()
                self.load_data()
            else:
                ModernMessageBox.critical(dialog, "失败", f"保存失败: {resp_data.get('message', '未知错误')}")
                
        save_btn.clicked.connect(save)
        dialog.exec()

    def toggle_status(self, user):
        new_status = 0 if user['status'] == 1 else 1
        res = api_client.patch(f"/users/{user['id']}/status", params={"status": new_status})
        resp_data = api_client.safe_json(res) or {}
        if res.status_code == 200 and resp_data.get('code') == 200:
            ModernMessageBox.information(self, "成功", "状态已更新")
            self.load_data()
        else:
            ModernMessageBox.critical(self, "失败", f"更新失败: {resp_data.get('message', '未知错误')}")

class LogView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_LG_INT)
        
        # 顶部操作栏
        top_card = ModernCard()
        top_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        top_layout = QHBoxLayout()
        
        title_label = ModernLabel("系统操作日志", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        self.search_input = ModernInput(placeholder="搜索操作内容...")
        self.search_input.setFixedWidth(250)
        top_layout.addWidget(self.search_input)
        
        search_btn = ModernButton("查询", variant="primary")
        search_btn.clicked.connect(self.load_data)
        top_layout.addWidget(search_btn)
        
        del_all_btn = ModernButton("清空所有日志", variant="danger")
        del_all_btn.clicked.connect(self.delete_all_logs)
        top_layout.addWidget(del_all_btn)
        
        top_card.add_layout(top_layout)
        layout.addWidget(top_card)
        
        # 数据表格区域
        table_card = ModernCard()
        table_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        self.table = ModernTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "操作内容", "操作数据", "操作人", "角色", "时间", "操作"])
        
        # 表格样式优化
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # 表头样式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID列自适应
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # 时间列自适应

        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {GRAY_50};
                color: {GRAY_600};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {GRAY_200};
                font-weight: bold;
            }}
        """)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {WHITE};
                border: none;
                gridline-color: {GRAY_200};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {GRAY_100};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR}10;
                color: {PRIMARY_COLOR};
            }}
            QTableWidget::item:alternate {{
                background-color: {GRAY_50};
            }}
        """)
        
        table_card.add_widget(self.table)
        layout.addWidget(table_card)
        
        self.setLayout(layout)

    def load_data(self):
        keyword = self.search_input.text()
        res = api_client.get("/operation-logs", params={"keyword": keyword, "size": 100})
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.logs = data['data']['records']
                self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.logs))
        for r, log in enumerate(self.logs):
            self.table.setItem(r, 0, QTableWidgetItem(str(log['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(log['action']))
            
            # 显示操作数据
            operate_data = log.get('operateData')
            if operate_data is None: operate_data = ""
            # 如果太长可以截断显示，或者用 tooltip
            data_item = QTableWidgetItem(operate_data)
            data_item.setToolTip(operate_data)
            self.table.setItem(r, 2, data_item)
            
            self.table.setItem(r, 3, QTableWidgetItem(log.get('username', '-')))
            self.table.setItem(r, 4, QTableWidgetItem(log.get('role', '-')))
            self.table.setItem(r, 5, QTableWidgetItem(str(log['createdAt'])))
            
            # 详情按钮
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            detail_btn = ModernButton("查看", variant="secondary")
            detail_btn.setFixedSize(60, 40)
            detail_btn.setStyleSheet(detail_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            detail_btn.clicked.connect(lambda _, l=log: self.show_detail_dialog(l))
            
            btn_layout.addWidget(detail_btn)
            self.table.setCellWidget(r, 6, btn_container)
            self.table.setRowHeight(r, 50)
            row_count = self.table.rowCount()
            for row in range(row_count):
                self.table.setRowHeight(row, 60)
    def show_detail_dialog(self, log):
        from PyQt6.QtWidgets import QTextEdit, QScrollArea
        
        dialog = QDialog(self)
        dialog.setWindowTitle("日志详情")
        dialog.setFixedSize(600, 500)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 使用 ModernCard 作为内容容器，营造卡片感
        card = ModernCard()
        # ModernCard 默认有 layout，我们需要把内容加进去
        
        # 顶部：标题和时间
        top_layout = QHBoxLayout()
        title = ModernLabel(f"操作详情 #{log['id']}", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=PRIMARY_COLOR)
        time_lbl = ModernLabel(str(log['createdAt']), color=GRAY_500, size=FONT_SIZE_SM)
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(time_lbl)
        
        card.add_layout(top_layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {GRAY_200}; max-height: 1px;")
        card.add_widget(line)
        
        # 基本信息网格
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        # 辅助函数：创建信息项
        def create_info_item(label_text, value_text):
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(5)
            lbl = ModernLabel(label_text, color=GRAY_600, size=FONT_SIZE_XS)
            val = ModernLabel(value_text, color=GRAY_900, weight=FONT_WEIGHT_BOLD)
            val.setWordWrap(True)
            v_layout.addWidget(lbl)
            v_layout.addWidget(val)
            return container

        grid_layout.addWidget(create_info_item("操作内容", log['action']), 0, 0, 1, 2) # 跨两列
        grid_layout.addWidget(create_info_item("操作人", log.get('username', '-')), 1, 0)
        grid_layout.addWidget(create_info_item("角色", log.get('role', '-')), 1, 1)
        
        card.add_layout(grid_layout)
        
        # 操作数据区域
        card.add_widget(ModernLabel("操作数据详情", weight=FONT_WEIGHT_BOLD, color=GRAY_700))
        
        data_view = QTextEdit()
        data_view.setReadOnly(True)
        data_view.setPlainText(log.get('operateData', ''))
        data_view.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                padding: 10px;
                background-color: {GRAY_50};
                font-family: Consolas, monospace;
                font-size: {FONT_SIZE_SM};
                color: {GRAY_800};
            }}
        """)
        card.add_widget(data_view)
        
        main_layout.addWidget(card)
        
        # 底部关闭按钮
        close_btn = ModernButton("关闭", variant="secondary")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

    def delete_all_logs(self):
        reply = ModernMessageBox.question(self, "确认", "确定要清空所有日志吗？此操作不可恢复！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.delete("/operation-logs")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "所有日志已清空")
                self.load_data()
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")
