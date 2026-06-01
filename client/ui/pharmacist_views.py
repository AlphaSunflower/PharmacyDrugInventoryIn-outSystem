from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, 
                             QInputDialog, QDateEdit, QFormLayout, QLineEdit, QDialog,
                             QTabWidget, QComboBox, QFileDialog, QHeaderView, QFrame)
from PyQt6.QtCore import QDate, Qt, QTimer, QEvent
from PyQt6.QtGui import QColor, QIntValidator
from utils.api_client import api_client
from ui.style_constants import *
from ui.components import ModernButton, ModernInput, ModernLabel, ModernCard, ModernMessageBox, PaginationControl, SmartDateEdit, DepartmentFilterGroup, DrugSelectionDialog, DiagnosisSelectionDialog, ModernTable, ModernInputDialog

class DispenseView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()
        
        # 自动刷新定时器 (降低频率减轻服务器压力)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(8000) # 8秒刷新一次

    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)

    def auto_refresh(self):
        if self.isVisible():
            self.load_data()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        # 主卡片
        main_card = ModernCard()
        
        header = QHBoxLayout()
        header.addWidget(ModernLabel("待发药列表", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800))
        header.addStretch()
        refresh_btn = ModernButton("刷新", variant="outline")
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn)
        
        main_card.add_layout(header)
        
        self.table = ModernTable()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "患者姓名", "就诊日期", "状态", "详情", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 80)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 230)
        
        main_card.add_widget(self.table)
        
        self.pagination = PaginationControl()
        self.pagination.page_changed.connect(lambda: self.load_data())
        self.pagination.size_changed.connect(lambda: self.load_data())
        main_card.add_widget(self.pagination)
        
        layout.addWidget(main_card)
        self.setLayout(layout)

    def load_data(self):
        page = self.pagination.current_page
        size = self.pagination.page_size
        
        res = api_client.get("/visits", params={"status": "SUBMITTED", "page": page, "size": size})
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.records = data['data']['records']
                self.pagination.update_state(data['data']['current'], data['data']['pages'], data['data']['total'])
                self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.records))
        for r, item in enumerate(self.records):
            visit_id = item.get('id')
            patient_name = item.get('patientName')
            visit_date = item.get('visitDate')
            status = item.get('status')
            
            self.table.setItem(r, 0, QTableWidgetItem(str(visit_id)))
            self.table.setItem(r, 1, QTableWidgetItem(patient_name))
            self.table.setItem(r, 2, QTableWidgetItem(str(visit_date)))
            
            status_map = {
                'DRAFT': '草稿',
                'SUBMITTED': '待发药',
                'RETURNED': '已退回',
                'COMPLETED': '已完成',
                'CANCELED': '已取消'
            }
            status_text = status_map.get(status, status)
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(PRIMARY_COLOR))
            self.table.setItem(r, 3, status_item)
            
            drugs_str = ", ".join([f"{d.get('drugName', 'ID:'+str(d['drugId']))} x{d['quantity']}" for d in item.get('drugs', [])])
            self.table.setItem(r, 4, QTableWidgetItem(drugs_str))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setSpacing(5)
            
            detail_btn = ModernButton("详情", variant="secondary")
            detail_btn.setFixedSize(60, 40)
            detail_btn.setStyleSheet(detail_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            detail_btn.clicked.connect(lambda _, item=item: self.show_detail(item))

            ok_btn = ModernButton("发药", variant="primary")
            ok_btn.setFixedSize(60, 40)
            ok_btn.setStyleSheet(ok_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            ok_btn.clicked.connect(lambda _, vid=visit_id: self.dispense(vid))
            
            reject_btn = ModernButton("退回", variant="danger")
            reject_btn.setFixedSize(60, 40)
            reject_btn.setStyleSheet(reject_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            reject_btn.clicked.connect(lambda _, vid=visit_id: self.reject(vid))
            
            btn_layout.addWidget(detail_btn)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(reject_btn)
            btn_layout.addStretch()
            
            self.table.setCellWidget(r, 5, btn_container)
            self.table.setRowHeight(r, 70)

    def show_detail(self, visit_item):
        dialog = QDialog(self)
        dialog.setWindowTitle("发药详情")
        dialog.setFixedSize(800, 600)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. 基本信息
        info_group = QWidget()
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        status_map = {
            'DRAFT': '草稿',
            'SUBMITTED': '待发药',
            'RETURNED': '已退回',
            'COMPLETED': '已完成',
            'CANCELED': '已取消'
        }
        
        info_layout.addRow(ModernLabel("就诊ID:", weight=FONT_WEIGHT_BOLD), ModernLabel(str(visit_item.get('id'))))
        info_layout.addRow(ModernLabel("患者姓名:", weight=FONT_WEIGHT_BOLD), ModernLabel(visit_item.get('patientName')))
        info_layout.addRow(ModernLabel("部门:", weight=FONT_WEIGHT_BOLD), ModernLabel(visit_item.get('department') or ""))
        info_layout.addRow(ModernLabel("就诊日期:", weight=FONT_WEIGHT_BOLD), ModernLabel(str(visit_item.get('visitDate'))))
        info_layout.addRow(ModernLabel("状态:", weight=FONT_WEIGHT_BOLD), ModernLabel(status_map.get(visit_item.get('status'), visit_item.get('status'))))
        
        layout.addWidget(info_group)
        
        # 2. 药品列表
        layout.addWidget(ModernLabel("药品清单", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))
        
        table = ModernTable()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["药品ID", "药品名称", "规格", "数量", "金额"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        drugs = visit_item.get('drugs', [])
        table.setRowCount(len(drugs))
        
        total_amount = 0.0
        
        for r, d in enumerate(drugs):
            # 注意：这里假设后端返回的 drugs 包含了药品的详细信息，如价格、规格等。
            # 如果没有，可能需要额外查询或依赖后端完善返回结构。
            # 这里的金额计算依赖单价，如果后端未返回单价，默认为0
            try:
                price = float(d.get('price', 0))
            except (ValueError, TypeError):
                price = 0.0
                
            quantity = d.get('quantity', 0)
            amount = price * quantity
            
            # 如果后端直接返回了 amount，也可以优先使用
            # amount = float(d.get('amount', amount))
            
            total_amount += amount
            
            table.setItem(r, 0, QTableWidgetItem(str(d.get('drugId'))))
            table.setItem(r, 1, QTableWidgetItem(d.get('drugName', '')))
            table.setItem(r, 2, QTableWidgetItem(d.get('spec', ''))) 
            table.setItem(r, 3, QTableWidgetItem(str(quantity)))
            table.setItem(r, 4, QTableWidgetItem(f"{amount:.2f}"))
            table.setRowHeight(r, 50)
            
        layout.addWidget(table)
        
        # 3. 统计
        total_label = ModernLabel(f"总金额: {total_amount:.2f} 元", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=PRIMARY_COLOR)
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_label)
        
        # 4. 操作按钮
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        dispense_btn = ModernButton("确认发药", variant="primary")
        dispense_btn.clicked.connect(lambda: [self.dispense(visit_item.get('id')), dialog.accept()])
        
        reject_btn = ModernButton("退回", variant="danger")
        reject_btn.clicked.connect(lambda: [self.reject(visit_item.get('id')), dialog.accept()])
        
        close_btn = ModernButton("关闭", variant="secondary")
        close_btn.clicked.connect(dialog.reject)
        
        btn_box.addWidget(dispense_btn)
        btn_box.addWidget(reject_btn)
        btn_box.addWidget(close_btn)
        
        layout.addLayout(btn_box)
        
        dialog.exec()

    def dispense(self, visit_id):
        reply = ModernMessageBox.question(self, "确认", "确认库存充足并进行发药？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.post(f"/visits/{visit_id}/dispense")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "发药成功")
                self.load_data()
                # 通知其他视图刷新库存
                mw = self.window()
                if hasattr(mw, 'stock_changed'):
                    mw.stock_changed.emit()
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

    def reject(self, visit_id):
        dlg = ModernInputDialog(self, "退回原因", "请输入退回原因:")
        if dlg.exec() == QDialog.DialogCode.Accepted and (reason := dlg.get_text()):

            res = api_client.post(f"/visits/{visit_id}/return", {"reason": reason})
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "已退回给医师")
                self.load_data()
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

class DispenseHistoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.diagnosis_types = []
        self.selected_diag_id = None
        self.initUI()
        self.load_data()
        
    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        main_card = ModernCard()
        
        # 垂直布局包含两行筛选
        top_layout = QVBoxLayout()
        top_layout.setSpacing(10)
        
        # 第一行
        row1 = QHBoxLayout()
        row1.addWidget(ModernLabel("已发药记录", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800))
        row1.addStretch()
        
        # 筛选
        self.search_input = ModernInput(placeholder="搜索患者姓名...")
        self.search_input.setFixedWidth(200)
        
        self.start_date = SmartDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumDate(QDate(2000, 1, 1))
        self.start_date.setDate(QDate(2000, 1, 1)) # 默认为空
        self.start_date.setSpecialValueText(" ") # 显示为空白
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedWidth(140)
        
        self.end_date = SmartDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumDate(QDate(2000, 1, 1))
        self.end_date.setDate(QDate(2000, 1, 1)) # 默认为空
        self.end_date.setSpecialValueText(" ") # 显示为空白
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setFixedWidth(140)
        
        search_btn = ModernButton("查询", variant="primary")
        search_btn.clicked.connect(self.on_search)
        
        clear_btn = ModernButton("清空查询", variant="secondary")
        clear_btn.clicked.connect(self.reset_search)
        
        row1.addWidget(ModernLabel("患者姓名:"))
        row1.addWidget(self.search_input)
        row1.addSpacing(20)
        row1.addWidget(ModernLabel("就诊时间范围:"))
        row1.addWidget(self.start_date)
        row1.addWidget(ModernLabel("-"))
        row1.addWidget(self.end_date)
        row1.addWidget(search_btn)
        row1.addWidget(clear_btn)
        row1.addStretch()
        
        top_layout.addLayout(row1)
        
        # 第二行
        row2 = QHBoxLayout()
        
        self.drug_name_filter = ModernInput(placeholder="搜索药品名称...")
        self.drug_name_filter.setFixedWidth(200)
        self.drug_name_filter.returnPressed.connect(self.on_search)
        
        row2.addWidget(ModernLabel("药品名称:"))
        row2.addWidget(self.drug_name_filter)
        row2.addSpacing(20)
        
        self.diag_search_input = ModernInput(placeholder="点击选择诊断...")
        self.diag_search_input.setReadOnly(True)
        self.diag_search_input.setFixedWidth(200)
        self.diag_search_input.installEventFilter(self)
        
        self.custom_diag_input = ModernInput(placeholder="输入自定义诊断...")
        self.custom_diag_input.setFixedWidth(200)
        self.custom_diag_input.setVisible(False)
        
        # 加载诊断数据
        self.load_diagnosis_types()
        
        self.dept_filter = DepartmentFilterGroup()
        self.dept_filter.department_changed.connect(self.on_search)
        
        row2.addWidget(ModernLabel("诊断筛选:"))
        row2.addWidget(self.diag_search_input)
        row2.addWidget(self.custom_diag_input)
        row2.addSpacing(40)
        row2.addWidget(ModernLabel("部门筛选:"))
        row2.addWidget(self.dept_filter)
        row2.addStretch()
        
        top_layout.addLayout(row2)
        
        main_card.add_layout(top_layout)
        
        self.table = ModernTable()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "患者姓名", "就诊日期", "药品概览", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4,100)
        
        main_card.add_widget(self.table)
        
        self.pagination = PaginationControl()
        self.pagination.page_changed.connect(lambda: self.load_data())
        self.pagination.size_changed.connect(lambda: self.load_data())
        main_card.add_widget(self.pagination)
        
        layout.addWidget(main_card)
        self.setLayout(layout)

    def load_diagnosis_types(self):
        res = api_client.get("/diagnosis-types")
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.diagnosis_types = data['data']

    def reset_search(self):
        self.search_input.clear()
        self.drug_name_filter.clear()
        self.start_date.setDate(QDate(2000, 1, 1))
        self.end_date.setDate(QDate(2000, 1, 1))
        
        self.selected_diag_id = None
        self.diag_search_input.clear()
        self.custom_diag_input.clear()
        self.custom_diag_input.setVisible(False)
        
        self.dept_filter.reset_selection()
        self.on_search()

    def on_search(self):
        self.pagination.current_page = 1
        self.load_data()

    def load_data(self):
        page = self.pagination.current_page
        size = self.pagination.page_size
        
        start_date_val = self.start_date.date()
        end_date_val = self.end_date.date()
        
        start_str = ""
        if start_date_val > self.start_date.minimumDate():
            start_str = start_date_val.toString("yyyy-MM-dd")
            
        end_str = ""
        if end_date_val > self.end_date.minimumDate():
            end_str = end_date_val.toString("yyyy-MM-dd")
        
        diag_id = self.selected_diag_id
        custom_diag = None
        if diag_id == 'CUSTOM':
            diag_id = None
            custom_diag = self.custom_diag_input.text().strip()

        params = {
            "status": "COMPLETED", 
            "page": page,
            "size": size,
            "keyword": self.search_input.text(),
            "drugName": self.drug_name_filter.text().strip(),
            "startDate": start_str,
            "endDate": end_str,
            "diagnosisId": diag_id,
            "customDiagnosis": custom_diag,
            "department": self.dept_filter.selected_dept
        }
        res = api_client.get("/visits", params=params)
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.records = data['data']['records']
                self.pagination.update_state(data['data']['current'], data['data']['pages'], data['data']['total'])
                self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.records))
        for r, item in enumerate(self.records):
            visit_id = item.get('id')
            patient_name = item.get('patientName')
            visit_date = item.get('visitDate')
            
            self.table.setItem(r, 0, QTableWidgetItem(str(visit_id)))
            self.table.setItem(r, 1, QTableWidgetItem(patient_name))
            self.table.setItem(r, 2, QTableWidgetItem(str(visit_date)))
            
            drugs_str = ", ".join([f"{d.get('drugName', 'ID:'+str(d['drugId']))} x{d['quantity']}" for d in item.get('drugs', [])])
            self.table.setItem(r, 3, QTableWidgetItem(drugs_str))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            detail_btn = ModernButton("详情", variant="secondary")
            detail_btn.setFixedSize(60, 40)
            detail_btn.setStyleSheet(detail_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            detail_btn.clicked.connect(lambda _, item=item: self.show_detail(item))
            
            btn_layout.addWidget(detail_btn)
            
            self.table.setCellWidget(r, 4, btn_container)
            self.table.setRowHeight(r, 70)

    def eventFilter(self, source, event):
        if source == getattr(self, 'diag_search_input', None) and event.type() == QEvent.Type.MouseButtonPress:
            self.open_diagnosis_dialog()
            return True
        return super().eventFilter(source, event)

    def open_diagnosis_dialog(self):
        if not hasattr(self, 'diagnosis_types') or not self.diagnosis_types:
             self.load_diagnosis_types()
             
        dialog = DiagnosisSelectionDialog(self.diagnosis_types, self)
        if dialog.exec() == QMessageBox.DialogCode.Accepted and dialog.selected_diagnosis:
            diag = dialog.selected_diagnosis
            if diag['id'] == 'CUSTOM':
                self.selected_diag_id = 'CUSTOM'
                self.diag_search_input.setText("自定义诊断")
                self.custom_diag_input.setVisible(True)
                self.custom_diag_input.setFocus()
            else:
                self.selected_diag_id = diag['id']
                self.diag_search_input.setText(diag['name'])
                self.custom_diag_input.setVisible(False)
                self.custom_diag_input.clear()

    def show_detail(self, visit_item):
        dialog = QDialog(self)
        dialog.setWindowTitle("发药记录详情")
        dialog.setFixedSize(800, 600)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. 基本信息
        info_group = QWidget()
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        info_layout.addRow(ModernLabel("就诊ID:", weight=FONT_WEIGHT_BOLD), ModernLabel(str(visit_item.get('id'))))
        info_layout.addRow(ModernLabel("患者姓名:", weight=FONT_WEIGHT_BOLD), ModernLabel(visit_item.get('patientName')))
        info_layout.addRow(ModernLabel("部门:", weight=FONT_WEIGHT_BOLD), ModernLabel(visit_item.get('department') or ""))
        info_layout.addRow(ModernLabel("就诊日期:", weight=FONT_WEIGHT_BOLD), ModernLabel(str(visit_item.get('visitDate'))))
        info_layout.addRow(ModernLabel("状态:", weight=FONT_WEIGHT_BOLD), ModernLabel("已完成"))
        
        layout.addWidget(info_group)
        
        # 2. 药品列表
        layout.addWidget(ModernLabel("药品清单", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))
        
        table = ModernTable()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["药品ID", "药品名称", "规格", "数量", "金额"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        drugs = visit_item.get('drugs', [])
        table.setRowCount(len(drugs))
        
        total_amount = 0.0
        
        for r, d in enumerate(drugs):
            try:
                price = float(d.get('price', 0))
            except (ValueError, TypeError):
                price = 0.0
                
            quantity = d.get('quantity', 0)
            amount = price * quantity
            total_amount += amount
            
            table.setItem(r, 0, QTableWidgetItem(str(d.get('drugId'))))
            table.setItem(r, 1, QTableWidgetItem(d.get('drugName', '')))
            table.setItem(r, 2, QTableWidgetItem(d.get('spec', ''))) 
            table.setItem(r, 3, QTableWidgetItem(str(quantity)))
            table.setItem(r, 4, QTableWidgetItem(f"{amount:.2f}"))
            table.setRowHeight(r, 50)
            
        layout.addWidget(table)
        
        # 3. 统计
        total_label = ModernLabel(f"总金额: {total_amount:.2f} 元", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=PRIMARY_COLOR)
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_label)
        
        # 4. 关闭按钮
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        close_btn = ModernButton("关闭", variant="secondary")
        close_btn.clicked.connect(dialog.accept)
        
        btn_box.addWidget(close_btn)
        
        layout.addLayout(btn_box)
        
        dialog.exec()

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.task_id = None
        self.task_status = None 
        self.is_clearing_placeholder = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        main_card = ModernCard()
        
        # 顶部操作栏
        top_layout = QHBoxLayout()
        top_layout.addWidget(ModernLabel("月份:", color=GRAY_800))
        self.month_edit = QDateEdit()
        self.month_edit.setDisplayFormat("yyyy-MM")
        self.month_edit.setDate(QDate.currentDate())
        self.style_dateedit(self.month_edit)
        top_layout.addWidget(self.month_edit)
        
        gen_btn = ModernButton("生成/获取盘点任务", variant="primary")
        gen_btn.clicked.connect(self.generate_task)
        top_layout.addWidget(gen_btn)
        
        self.reopen_btn = ModernButton("重新修改", variant="warning")
        self.reopen_btn.clicked.connect(self.reopen_task)
        self.reopen_btn.setVisible(False)
        top_layout.addWidget(self.reopen_btn)
        
        self.delete_btn = ModernButton("删除任务", variant="danger")
        self.delete_btn.clicked.connect(self.delete_task)
        self.delete_btn.setVisible(False)
        top_layout.addWidget(self.delete_btn)
        
        self.complete_btn = ModernButton("完成本次盘点", variant="primary")
        self.complete_btn.clicked.connect(self.complete_task)
        top_layout.addWidget(self.complete_btn)
        
        top_layout.addStretch()
        main_card.add_layout(top_layout)
        
        # 盘点明细表格
        self.table = ModernTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "药品名称", "规格", "系统库存", "实盘数量", "差异", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        main_card.add_widget(self.table)
        
        layout.addWidget(main_card)
        self.setLayout(layout)

    def style_dateedit(self, date_edit):
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 5px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """)

    def generate_task(self):
        month = self.month_edit.date().toString("yyyy-MM")
        res = api_client.post("/inventory-checks/generate", params={"month": month})
        if res.status_code == 200 and res.json()['code'] == 200:
            self.task_id = res.json()['data']
            ModernMessageBox.information(self, "成功", f"已获取 {month} 月盘点任务，ID: {self.task_id}")
            self.load_details()
        else:
            ModernMessageBox.critical(self, "错误", f"获取任务失败: {res.json().get('message')}")

    def load_details(self):
        if not self.task_id: return
        res = api_client.get(f"/inventory-checks/{self.task_id}/details")
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.details = data['data']
                self.refresh_table()
                self.check_task_status()

    def check_task_status(self):
        res = api_client.get("/inventory-checks/pending")
        is_pending = False
        if res.status_code == 200 and res.json()['code'] == 200:
            pending_tasks = res.json()['data']
            for t in pending_tasks:
                if t['id'] == self.task_id:
                    is_pending = True
                    break
        
        if is_pending:
            self.complete_btn.setVisible(True)
            self.reopen_btn.setVisible(False)
            self.delete_btn.setVisible(True) # 允许删除进行中的任务以重新生成
            self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.AnyKeyPressed)
        else:
            self.complete_btn.setVisible(False)
            self.reopen_btn.setVisible(True)
            self.delete_btn.setVisible(True)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    def on_cell_double_clicked(self, row, col):
        if not self.task_id: return
        if col not in [4, 6]: return
        
        item = self.table.item(row, col)
        if item.text() == "点击填写" and item.foreground().color() == QColor(GRAY_400):
            self.is_clearing_placeholder = True
            item.setText("")
            item.setForeground(QColor(BLACK))
            self.is_clearing_placeholder = False

    def reopen_task(self):
        if not self.task_id: return
        reply = ModernMessageBox.question(self, "确认", "确定要重新开启盘点任务进行修改吗？", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.post(f"/inventory-checks/{self.task_id}/reopen")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "任务已重新开启")
                self.check_task_status()
                self.load_details()
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

    def delete_task(self):
        if not self.task_id: return
        reply = ModernMessageBox.question(self, "确认", "确定要删除该盘点任务吗？此操作不可恢复！", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.delete(f"/inventory-checks/{self.task_id}")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "任务已删除")
                self.task_id = None
                self.details = []
                self.table.setRowCount(0)
                self.complete_btn.setVisible(True)
                self.reopen_btn.setVisible(False)
                self.delete_btn.setVisible(False)
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.details))
        for r, item in enumerate(self.details):
            detail_id = item.get('id')
            drug_name = item.get('drugName')
            drug_spec = item.get('drugSpec')
            system_stock = item.get('systemStock')

            # 设置只读列: ID, 名称, 规格, 系统库存
            id_item = QTableWidgetItem(str(detail_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 0, id_item)

            name_item = QTableWidgetItem(drug_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 1, name_item)

            spec_item = QTableWidgetItem(drug_spec)
            spec_item.setFlags(spec_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 2, spec_item)

            sys_item = QTableWidgetItem(str(system_stock))
            sys_item.setFlags(sys_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 3, sys_item)
            
            actual = item.get('actualStock')
            actual_text = str(actual) if actual is not None else ""
            actual_item = QTableWidgetItem(actual_text)
            actual_item.setFlags(actual_item.flags() | Qt.ItemFlag.ItemIsEditable)
            if not actual_text:
                actual_item.setText("点击填写")
                actual_item.setForeground(QColor(GRAY_400))
            self.table.setItem(r, 4, actual_item)
            
            diff = item.get('discrepancy')
            diff_item = QTableWidgetItem(str(diff) if diff is not None else "")
            diff_item.setFlags(diff_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if diff and diff != 0:
                diff_item.setForeground(QColor(ERROR_COLOR))
            self.table.setItem(r, 5, diff_item)
            
            remark_text = item.get('remark') or ""
            remark_item = QTableWidgetItem(remark_text)
            remark_item.setFlags(remark_item.flags() | Qt.ItemFlag.ItemIsEditable)
            if not remark_text:
                 remark_item.setText("点击填写")
                 remark_item.setForeground(QColor(GRAY_400))
            self.table.setItem(r, 6, remark_item)
            
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, detail_id)
            self.table.setRowHeight(r, 50)
            
        self.table.blockSignals(False)

    def on_cell_changed(self, row, col):
        if getattr(self, 'is_clearing_placeholder', False): return

        if not self.task_id: return
        if col not in [4, 6]: return
        
        detail_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item = self.table.item(row, col)
        
        # 如果内容是占位符，不处理
        if item.text() == "点击填写" and item.foreground().color() == QColor(GRAY_400):
            return

        # 如果内容被清空，恢复占位符
        if item.text().strip() == "":
            self.table.blockSignals(True)
            item.setText("点击填写")
            item.setForeground(QColor(GRAY_400))
            self.table.blockSignals(False)
            # 继续执行以更新后端数据为 None

        # 获取真实值（排除占位符）
        actual_item = self.table.item(row, 4)
        actual_text = actual_item.text()
        if actual_text == "点击填写" and actual_item.foreground().color() == QColor(GRAY_400):
            actual_text = ""
            
        remark_item = self.table.item(row, 6)
        remark = remark_item.text()
        if remark == "点击填写" and remark_item.foreground().color() == QColor(GRAY_400):
            remark = ""
        
        actual_val = None
        if actual_text.isdigit():
            actual_val = int(actual_text)
        elif actual_text == "":
             pass # 允许为空
        else:
            ModernMessageBox.warning(self, "提示", "实盘数量必须为数字")
            # 恢复之前的值或占位符
            self.table.blockSignals(True)
            if col == 4:
                item.setText("点击填写")
                item.setForeground(QColor(GRAY_400))
            self.table.blockSignals(False)
            return

        data = {
            "actualStock": actual_val,
            "remark": remark
        }
        api_client.put(f"/inventory-checks/details/{detail_id}", data)
        sys_stock = int(self.table.item(row, 3).text())
        
        self.table.blockSignals(True)
        if actual_val is not None:
            diff = actual_val - sys_stock
            diff_item = QTableWidgetItem(str(diff))
            diff_item.setFlags(diff_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if diff != 0:
                 diff_item.setForeground(QColor(ERROR_COLOR))
            self.table.setItem(row, 5, diff_item)
            
            # 设置正常颜色
            actual_item.setForeground(QColor(BLACK))
        else:
            empty_diff = QTableWidgetItem("")
            empty_diff.setFlags(empty_diff.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, empty_diff)
            
        if remark:
            remark_item.setForeground(QColor(BLACK))
            
        self.table.blockSignals(False)

    def complete_task(self):
        if not self.task_id: return
        res = api_client.post(f"/inventory-checks/{self.task_id}/complete")
        if res.status_code == 200 and res.json()['code'] == 200:
            ModernMessageBox.information(self, "成功", "盘点任务已完成")
            self.check_task_status()
        else:
            ModernMessageBox.critical(self, "失败", f"提交失败: {res.json().get('message')}")

class DrugManageView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()
        # 延迟连接信号，等 widget 加入 MainWindow 层级后再绑定
        QTimer.singleShot(0, self._connect_stock_signal)

    def _connect_stock_signal(self):
        mw = self.window()
        if hasattr(mw, 'stock_changed'):
            mw.stock_changed.connect(self.load_data)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        main_card = ModernCard()
        
        top = QHBoxLayout()
        self.search_input = ModernInput(placeholder="搜索药品名称...")
        self.search_input.setFixedWidth(200)
        
        self.min_stock_input = ModernInput(placeholder="最小库存")
        self.min_stock_input.setFixedWidth(100)
        self.min_stock_input.setValidator(QIntValidator(0, 999999))
        
        self.max_stock_input = ModernInput(placeholder="最大库存")
        self.max_stock_input.setFixedWidth(100)
        self.max_stock_input.setValidator(QIntValidator(0, 999999))
        
        search_btn = ModernButton("查询", variant="primary")
        search_btn.clicked.connect(self.on_search)
        
        clear_btn = ModernButton("清空查询", variant="secondary")
        clear_btn.clicked.connect(self.reset_search)
        
        add_btn = ModernButton("新增药品", variant="secondary")
        add_btn.clicked.connect(self.show_add_dialog)
        
        top.addWidget(ModernLabel("药品名称:"))
        top.addWidget(self.search_input)
        top.addSpacing(20)
        top.addWidget(ModernLabel("库存范围:"))
        top.addWidget(self.min_stock_input)
        top.addWidget(ModernLabel("-"))
        top.addWidget(self.max_stock_input)
        top.addWidget(search_btn)
        top.addWidget(clear_btn)
        top.addWidget(add_btn)
        top.addStretch()
        
        main_card.add_layout(top)
        
        self.table = ModernTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "规格", "单位", "价格", "库存", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 60)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 80)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 80)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 230)
        
        main_card.add_widget(self.table)
        
        self.pagination = PaginationControl()
        self.pagination.page_changed.connect(lambda: self.load_data())
        self.pagination.size_changed.connect(lambda: self.load_data())
        main_card.add_widget(self.pagination)
        
        layout.addWidget(main_card)
        self.setLayout(layout)

    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)

    def reset_search(self):
        self.search_input.clear()
        self.min_stock_input.clear()
        self.max_stock_input.clear()
        self.on_search()

    def on_search(self):
        self.pagination.current_page = 1
        self.load_data()

    def load_data(self):
        page = self.pagination.current_page
        size = self.pagination.page_size
        keyword = self.search_input.text()
        
        params = {"keyword": keyword, "page": page, "size": size}
        
        if self.min_stock_input.text().strip():
            params["minStock"] = self.min_stock_input.text().strip()
        if self.max_stock_input.text().strip():
            params["maxStock"] = self.max_stock_input.text().strip()
            
        res = api_client.get("/drugs", params=params)
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.drugs = data['data']['records']
                self.pagination.update_state(data['data']['current'], data['data']['pages'], data['data']['total'])
                self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(len(self.drugs))
        for r, d in enumerate(self.drugs):
            self.table.setItem(r, 0, QTableWidgetItem(str(d['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(d['name']))
            self.table.setItem(r, 2, QTableWidgetItem(d['spec']))
            self.table.setItem(r, 3, QTableWidgetItem(d['unit']))
            self.table.setItem(r, 4, QTableWidgetItem(str(d['price'])))
            self.table.setItem(r, 5, QTableWidgetItem(str(d.get('stockQuantity', 0))))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setSpacing(1)
            
            detail_btn = ModernButton("详情", variant="primary")
            detail_btn.setFixedSize(60, 40)
            detail_btn.setStyleSheet(detail_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            detail_btn.clicked.connect(lambda _, drug=d: self.show_detail_dialog(drug))
            
            edit_btn = ModernButton("修改", variant="secondary")
            edit_btn.setFixedSize(60, 40)
            edit_btn.setStyleSheet(edit_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            edit_btn.clicked.connect(lambda _, drug=d: self.show_edit_dialog(drug))
            
            del_btn = ModernButton("删除", variant="danger")
            del_btn.setFixedSize(60, 40)
            del_btn.setStyleSheet(del_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            del_btn.clicked.connect(lambda _, drug_id=d['id']: self.delete_drug(drug_id))
            
            btn_layout.addWidget(detail_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            
            self.table.setCellWidget(r, 6, btn_container)
            self.table.setRowHeight(r, 65)

    def delete_drug(self, drug_id):
        reply = ModernMessageBox.question(self, "确认", "确定要删除该药品吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.delete(f"/drugs/{drug_id}")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "删除成功")
                self.load_data()
            else:
                ModernMessageBox.critical(self, "失败", f"删除失败: {res.json().get('message')}")

    def show_detail_dialog(self, drug):
        dialog = QDialog(self)
        dialog.setWindowTitle("药品详情")
        dialog.setFixedSize(600, 500)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. 基本信息
        info_group = QWidget()
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        info_layout.addRow(ModernLabel("药品名称:", weight=FONT_WEIGHT_BOLD), ModernLabel(drug.get('name', '')))
        info_layout.addRow(ModernLabel("规格:", weight=FONT_WEIGHT_BOLD), ModernLabel(drug.get('spec', '')))
        info_layout.addRow(ModernLabel("单位:", weight=FONT_WEIGHT_BOLD), ModernLabel(drug.get('unit', '')))
        info_layout.addRow(ModernLabel("零售价格:", weight=FONT_WEIGHT_BOLD), ModernLabel(f"{drug.get('price', 0)} 元"))
        info_layout.addRow(ModernLabel("总库存:", weight=FONT_WEIGHT_BOLD), ModernLabel(str(drug.get('stockQuantity', 0))))
        
        layout.addWidget(info_group)
        
        # 2. 批次列表
        layout.addWidget(ModernLabel("库存批次信息", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))
        
        table = ModernTable()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["批次号", "进价", "剩余库存", "有效期"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        batches = drug.get('batchList', [])
        table.setRowCount(len(batches))
        
        for r, b in enumerate(batches):
            table.setItem(r, 0, QTableWidgetItem(b.get('batchNo') or "-"))
            table.setItem(r, 1, QTableWidgetItem(str(b.get('price', 0))))
            table.setItem(r, 2, QTableWidgetItem(str(b.get('stockQuantity', 0))))
            table.setItem(r, 3, QTableWidgetItem(str(b.get('expiryDate') or "未设置")))
            table.setRowHeight(r, 45)
            
        layout.addWidget(table)
        
        # 3. 关闭按钮
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = ModernButton("关闭", variant="secondary")
        close_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(close_btn)
        
        layout.addLayout(btn_box)
        dialog.exec()

    def show_add_dialog(self):
        self.show_drug_dialog("新增药品")

    def show_edit_dialog(self, drug):
        self.show_drug_dialog("修改药品", drug)

    def show_drug_dialog(self, title, drug=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 400)
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        name_edit = ModernInput(placeholder="请输入名称")
        spec_edit = ModernInput(placeholder="请输入规格")
        unit_edit = ModernInput(placeholder="请输入单位")
        price_edit = ModernInput(placeholder="请输入价格")
        
        if drug:
            name_edit.setText(drug['name'])
            spec_edit.setText(drug['spec'])
            unit_edit.setText(drug['unit'])
            price_edit.setText(str(drug['price']))
        
        stock_edit = None
        batch_combo = None
        current_batch_id = None

        if drug:
            stock_edit = ModernInput(placeholder="请输入库存")
            batches = drug.get('batchList', [])
            
            if len(batches) > 1:
                batch_combo = QComboBox()
                batch_combo.setStyleSheet(f"padding: 8px; border: 1px solid {GRAY_300}; border-radius: {RADIUS_BASE}; background-color: {WHITE};")
                for b in batches:
                    batch_combo.addItem(f"批次:{b.get('batchNo', 'N/A')} (余:{b['stockQuantity']})", b)
                
                def on_batch_changed(index):
                    b = batch_combo.itemData(index)
                    stock_edit.setText(str(b['stockQuantity']))
                
                batch_combo.currentIndexChanged.connect(on_batch_changed)
                # Init with first batch
                if batches:
                    stock_edit.setText(str(batches[0]['stockQuantity']))
                
            elif len(batches) == 1:
                current_batch_id = batches[0]['id']
                stock_edit.setText(str(batches[0]['stockQuantity']))
            else:
                # No batches - fallback to total stock
                stock_edit.setText(str(drug.get('stockQuantity', 0)))
        
        form_layout.addRow(ModernLabel("名称:"), name_edit)
        form_layout.addRow(ModernLabel("规格:"), spec_edit)
        form_layout.addRow(ModernLabel("单位:"), unit_edit)
        form_layout.addRow(ModernLabel("价格:"), price_edit)
        if drug:
            if batch_combo:
                form_layout.addRow(ModernLabel("选择批次:"), batch_combo)
            form_layout.addRow(ModernLabel("库存:"), stock_edit)
            
        layout.addLayout(form_layout)
        
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
                "name": name_edit.text(),
                "spec": spec_edit.text(),
                "unit": unit_edit.text(),
                "price": float(price_edit.text() or 0)
            }
            
            stock_updated_via_batch = False

            if stock_edit and drug:
                try:
                    new_stock = int(stock_edit.text())
                    
                    # Determine target batch
                    target_batch_id = None
                    if batch_combo:
                        target_batch_id = batch_combo.currentData()['id']
                    elif current_batch_id:
                        target_batch_id = current_batch_id
                    
                    # Check if change needed
                    should_update = False
                    if target_batch_id:
                        # Find original stock for comparison
                        original_stock = 0
                        batches = drug.get('batchList', [])
                        for b in batches:
                            if b['id'] == target_batch_id:
                                original_stock = b['stockQuantity']
                                break
                        if new_stock != original_stock:
                            should_update = True
                    else:
                        if new_stock != drug.get('stockQuantity', 0):
                            should_update = True
                            data['stockQuantity'] = new_stock

                    if should_update:
                        msg = ModernMessageBox(dialog)
                        msg.setWindowTitle("修改库存确认")
                        msg.setText("您正在修改药品库存。请注意：如果是想购进药品，请到‘药品购进’模块进行购进操作。")
                        msg.setIcon(QMessageBox.Icon.Warning)
                        yes_btn = msg.addButton("确认修改", QMessageBox.ButtonRole.AcceptRole)
                        no_btn = msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
                        
                        yes_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {PRIMARY_COLOR};
                                color: {WHITE};
                                border: none;
                                padding: 6px 20px;
                                border-radius: {RADIUS_BASE};
                            }}
                            QPushButton:hover {{
                                background-color: {PRIMARY_HOVER_COLOR};
                            }}
                        """)
                        no_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {WHITE};
                                color: {GRAY_700};
                                border: 1px solid {GRAY_300};
                                padding: 6px 20px;
                                border-radius: {RADIUS_BASE};
                            }}
                            QPushButton:hover {{
                                background-color: {GRAY_50};
                            }}
                        """)
                        
                        msg.exec()
                        
                        if msg.clickedButton() == no_btn:
                            return
                            
                        # Execute Batch Update if applicable
                        if target_batch_id:
                             # Use params for query parameters
                             res_batch = api_client.put(f"/drugs/batch/{target_batch_id}/stock", params={"quantity": new_stock})
                             if res_batch.status_code == 200 and res_batch.json()['code'] == 200:
                                 stock_updated_via_batch = True
                             else:
                                 ModernMessageBox.critical(dialog, "失败", f"更新批次库存失败: {res_batch.json().get('message')}")
                                 return

                except ValueError:
                    ModernMessageBox.warning(dialog, "提示", "库存数量必须为整数")
                    return

            if drug:
                res = api_client.put(f"/drugs/{drug['id']}", data)
            else:
                res = api_client.post("/drugs", data)
                
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(dialog, "成功", "保存成功")
                dialog.accept()
                self.load_data()
            else:
                ModernMessageBox.critical(dialog, "失败", f"保存失败: {res.json().get('message')}")
                
        save_btn.clicked.connect(save)
        dialog.exec()

class PurchaseView(QWidget):
    def __init__(self):
        super().__init__()
        self.drugs = []
        self.purchase_list = []
        self.existing_list = []
        self.selected_drug_id = None
        self.initUI()
        
        self.load_purchases()
        
        self.installEventFilter(self)

    def showEvent(self, event):
        self.load_purchases()
        super().showEvent(event)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        # 1. 顶部月份选择
        top_card = ModernCard()
        top_bar = QHBoxLayout()
        top_bar.addWidget(ModernLabel("选择月份:", color=GRAY_800))
        self.month_filter = QDateEdit()
        self.month_filter.setDisplayFormat("yyyy-MM")
        self.month_filter.setDate(QDate.currentDate())
        self.style_dateedit(self.month_filter)
        self.month_filter.dateChanged.connect(self.load_purchases)
        top_bar.addWidget(self.month_filter)
        
        self.search_input = ModernInput(placeholder="搜索药品名称...")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self.load_purchases)
        top_bar.addWidget(self.search_input)
        
        refresh_btn = ModernButton("查询", variant="outline")
        refresh_btn.clicked.connect(self.load_purchases)
        top_bar.addWidget(refresh_btn)
        top_bar.addStretch()
        top_card.add_layout(top_bar)
        layout.addWidget(top_card)

        # 2. 新增表单
        form_card = ModernCard()
        form_card.add_widget(ModernLabel("新增购进登记", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD))
        
        form_layout = QHBoxLayout()
        
        # 药品搜索组件
        self.drug_search_container = QWidget()
        drug_search_layout = QHBoxLayout(self.drug_search_container)
        drug_search_layout.setContentsMargins(0, 0, 0, 0)
        drug_search_layout.setSpacing(5)

        self.drug_search_input = ModernInput(placeholder="点击选择药品...")
        self.drug_search_input.setFixedWidth(200)
        self.drug_search_input.setReadOnly(True)
        self.drug_search_input.installEventFilter(self)

        drug_search_layout.addWidget(self.drug_search_input)

        self.quantity_input = ModernInput(placeholder="数量")
        self.quantity_input.setFixedWidth(100)
        
        self.unit_input = ModernInput(placeholder="单位")
        self.unit_input.setFixedWidth(60)
        self.unit_input.setReadOnly(True)
        
        self.amount_input = ModernInput(placeholder="总金额")
        self.amount_input.setFixedWidth(120)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.style_dateedit(self.date_input)
        
        add_btn = ModernButton("添加待提交", variant="secondary")
        add_btn.clicked.connect(self.add_to_list)
        
        form_layout.addWidget(ModernLabel("药品:"))
        form_layout.addWidget(self.drug_search_container)
        form_layout.addWidget(ModernLabel("数量:"))
        form_layout.addWidget(self.quantity_input)
        form_layout.addWidget(self.unit_input)
        form_layout.addWidget(ModernLabel("总金额:"))
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(ModernLabel("日期:"))
        form_layout.addWidget(self.date_input)
        form_layout.addWidget(add_btn)
        form_layout.addStretch()
        
        form_card.add_layout(form_layout)
        layout.addWidget(form_card)
        
        # 3. 列表
        table_card = ModernCard()
        self.table = ModernTable()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["状态", "日期", "药品名称", "数量", "单位", "总金额", "单价", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        table_card.add_widget(self.table)
        layout.addWidget(table_card)
        
        # 4. 底部提交按钮
        submit_btn = ModernButton("提交新增记录", variant="primary")
        submit_btn.clicked.connect(self.submit_batch_purchase)
        layout.addWidget(submit_btn)
        
        self.setLayout(layout)

    def style_dateedit(self, date_edit):
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 5px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """)

    def style_combobox(self, combo):
        combo.setStyleSheet(f"""
            QComboBox {{
                padding: 5px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
        """)

    def load_purchases(self):
        month = self.month_filter.date().toString("yyyy-MM")
        keyword = self.search_input.text().strip()
        
        params = {"month": month}
        if keyword:
            params["drugName"] = keyword
            
        res = api_client.get("/purchases", params=params)
        if res.status_code == 200 and res.json()['code'] == 200:
            self.existing_list = res.json()['data']
            self.refresh_list_table()

    def open_drug_selection_dialog(self):
        dialog = DrugSelectionDialog(self)
        if dialog.exec() == QMessageBox.DialogCode.Accepted and dialog.selected_drug:
            drug = dialog.selected_drug
            self.selected_drug_id = drug['id']
            self.drug_search_input.setText(f"{drug['name']} ({drug['spec']})")
            self.unit_input.setText(drug['unit'])

    def eventFilter(self, source, event):
        if source == self.drug_search_input and event.type() == QEvent.Type.MouseButtonPress:
            self.open_drug_selection_dialog()
            return True

        return super().eventFilter(source, event)

    def add_to_list(self):
        drug_id = self.selected_drug_id
        drug_name = self.drug_search_input.text()
        qty = self.quantity_input.text()
        total_amount = self.amount_input.text()
        
        if not drug_id:
            ModernMessageBox.warning(self, "提示", "请先选择药品")
            return
        
        if not qty.isdigit() or int(qty) <= 0:
            ModernMessageBox.warning(self, "提示", "请输入有效的数量")
            return
            
        try:
            amount_val = float(total_amount)
            if amount_val <= 0: raise ValueError
        except:
            ModernMessageBox.warning(self, "提示", "请输入有效的总金额")
            return
            
        unit_price = amount_val / int(qty)
        
        self.purchase_list.append({
            "drugId": drug_id,
            "drugName": drug_name,
            "quantity": int(qty),
            "unit": self.unit_input.text(),
            "totalAmount": amount_val,
            "price": unit_price, 
            "purchaseDate": self.date_input.date().toString("yyyy-MM-dd")
        })
        
        self.refresh_list_table()
        
        self.quantity_input.clear()
        self.amount_input.clear()
        self.drug_search_input.clear()
        self.unit_input.clear()
        self.selected_drug_id = None

    def refresh_list_table(self):
        total_rows = len(self.existing_list) + len(self.purchase_list)
        self.table.setRowCount(total_rows)

        # 1. 显示待提交 (Pending)
        for i, item in enumerate(self.purchase_list):
            self.table.setItem(i, 0, QTableWidgetItem("待提交"))
            self.table.item(i, 0).setBackground(QColor(WARNING_COLOR))
            self.table.item(i, 0).setForeground(QColor("pink"))
            self.table.setItem(i, 1, QTableWidgetItem(item['purchaseDate']))
            self.table.setItem(i, 2, QTableWidgetItem(item['drugName']))
            self.table.setItem(i, 3, QTableWidgetItem(str(item['quantity'])))
            self.table.setItem(i, 4, QTableWidgetItem(item['unit']))
            self.table.setItem(i, 5, QTableWidgetItem(f"{item['totalAmount']:.2f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{item['price']:.2f}"))

            del_btn = ModernButton("删除", variant="danger")
            del_btn.setFixedSize(60, 40)
            del_btn.setStyleSheet(del_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            del_btn.clicked.connect(lambda _, row=i: self.remove_item(row))

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0,0,0,0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(del_btn)

            self.table.setCellWidget(i, 7, container)
            self.table.setRowHeight(i, 70)

        # 2. 显示已存在 (Existing)
        offset = len(self.purchase_list)
        for i, item in enumerate(self.existing_list):
            row = offset + i
            self.table.setItem(row, 0, QTableWidgetItem("已入库"))
            self.table.item(row, 0).setBackground(QColor(SUCCESS_COLOR))
            self.table.item(row, 0).setForeground(QColor("green"))
            
            p_date = item.get('purchaseDate')
            self.table.setItem(row, 1, QTableWidgetItem(str(p_date)))
            self.table.setItem(row, 2, QTableWidgetItem(item.get('drugName', '')))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get('quantity', 0))))
            self.table.setItem(row, 4, QTableWidgetItem(item.get('unit', '')))
            self.table.setItem(row, 5, QTableWidgetItem(str(item.get('totalAmount', 0))))
            self.table.setItem(row, 6, QTableWidgetItem(str(item.get('price', 0))))
            
            self.table.removeCellWidget(row, 7) # 清除可能存在的按钮
            self.table.setItem(row, 7, QTableWidgetItem("-"))
            self.table.item(row, 7).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setRowHeight(row, 70)

    def remove_item(self, row):
        if row < len(self.purchase_list):
            self.purchase_list.pop(row)
            self.refresh_list_table()

    def submit_batch_purchase(self):
        if not self.purchase_list:
            ModernMessageBox.warning(self, "提示", "没有待提交的新记录")
            return
            
        submit_data = []
        for item in self.purchase_list:
            submit_data.append({
                "drugId": item['drugId'],
                "quantity": item['quantity'],
                "unit": item['unit'],
                "price": item['price'],
                "totalAmount": item['totalAmount'],
                "purchaseDate": item['purchaseDate']
            })
        
        res = api_client.post("/purchases/batch", submit_data)
        if res.status_code == 200 and res.json()['code'] == 200:
            ModernMessageBox.information(self, "成功", "购进记录已保存")
            self.purchase_list = []
            self.load_purchases()
            # 通知其他视图刷新库存
            mw = self.window()
            if hasattr(mw, 'stock_changed'):
                mw.stock_changed.emit()
        else:
            ModernMessageBox.critical(self, "失败", f"提交失败: {res.json().get('message')}")

class StatsView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        main_card = ModernCard()
        
        # 顶部过滤
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(ModernLabel("月份:", color=GRAY_800))
        self.month_edit = QDateEdit()
        self.month_edit.setDisplayFormat("yyyy-MM")
        self.month_edit.setDate(QDate.currentDate())
        self.style_dateedit(self.month_edit)
        filter_layout.addWidget(self.month_edit)
        
        query_btn = ModernButton("查询报表", variant="primary")
        query_btn.clicked.connect(self.load_stats)
        filter_layout.addWidget(query_btn)
        
        export_btn = ModernButton("导出Excel", variant="secondary")
        export_btn.clicked.connect(self.export_stats)
        filter_layout.addWidget(export_btn)
        
        filter_layout.addStretch()
        main_card.add_layout(filter_layout)
        
        # 选项卡
        # 跟踪已加载的 tab，懒加载避免一次性 4 个 API 调用阻塞 UI
        self._loaded_tabs = set()
        self._current_month = None

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {GRAY_200};
                border-radius: {RADIUS_BASE};
                background: {WHITE};
            }}
            QTabBar::tab {{
                background: {GRAY_50};
                color: {GRAY_600};
                padding: 10px 20px;
                border: 1px solid {GRAY_200};
                border-bottom: none;
                border-top-left-radius: {RADIUS_BASE};
                border-top-right-radius: {RADIUS_BASE};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {WHITE};
                color: {PRIMARY_COLOR};
                font-weight: bold;
                border-bottom: 2px solid {PRIMARY_COLOR};
            }}
        """)
        
        self.drug_stats_tab = ModernTable()
        
        self.op_stats_tab = QWidget()

        self.monthly_summary_tab = ModernTable()

        # 年度汇总报表容器
        self.yearly_summary_container = QWidget()
        yearly_layout = QVBoxLayout(self.yearly_summary_container)
        yearly_layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        self.yearly_warning_label = ModernLabel("", color=ERROR_COLOR)
        self.yearly_warning_label.setVisible(False)
        yearly_layout.addWidget(self.yearly_warning_label)
        
        self.yearly_summary_tab = ModernTable()
        yearly_layout.addWidget(self.yearly_summary_tab)
        
        self.tabs.addTab(self.drug_stats_tab, "药品进销存月报")
        self.tabs.addTab(self.op_stats_tab, "运营统计月报")
        self.tabs.addTab(self.monthly_summary_tab, "月度汇总报表")
        self.tabs.addTab(self.yearly_summary_container, "年度汇总报表")
        
        main_card.add_widget(self.tabs)
        layout.addWidget(main_card)
        
        self.setLayout(layout)

        self.drug_stats_tab.setColumnCount(6)
        self.drug_stats_tab.setHorizontalHeaderLabels(["药品", "规格", "期初", "本月购进", "本月使用", "期末"])
        
        self.monthly_summary_tab.setColumnCount(8)
        self.monthly_summary_tab.setHorizontalHeaderLabels([
            "部门", "接诊人数", "处方开出金额", "外伤处理金额", 
            "领导拿药金额", "期初库存金额", "药品采购总金额", "期末库存金额"
        ])
        self.monthly_summary_tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.yearly_summary_tab.setColumnCount(8)
        self.yearly_summary_tab.setHorizontalHeaderLabels([
            "部门", "接诊人数", "处方开出金额", "外伤处理金额", 
            "领导拿药金额", "期初库存金额", "药品采购总金额", "期末库存金额"
        ])
        self.yearly_summary_tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def style_dateedit(self, date_edit):
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 5px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """)

    def export_stats(self):
        month = self.month_edit.date().toString("yyyy-MM")
        year = self.month_edit.date().toString("yyyy")
        current_tab_idx = self.tabs.currentIndex()
        
        params = {"month": month}
        
        if current_tab_idx == 0:
            url = "/stats/drugs/export"
            default_name = f"药品进销存报表_{month}.xlsx"
        elif current_tab_idx == 1:
            url = "/stats/operations/export"
            default_name = f"运营统计报表_{month}.xlsx"
        elif current_tab_idx == 2:
            url = "/stats/monthly-summary/export"
            default_name = f"月度汇总报表_{month}.xlsx"
        elif current_tab_idx == 3:
            url = "/stats/yearly-summary/export"
            default_name = f"年度汇总报表_{year}.xlsx"
            params = {"year": year}
        else:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", default_name, "Excel Files (*.xlsx)")
        if not file_path:
            return
            
        try:
            res = api_client.get(url, params=params)
            
            if res.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(res.content)
                ModernMessageBox.information(self, "成功", "导出成功")
            else:
                ModernMessageBox.critical(self, "失败", f"导出失败: {res.status_code}")
        except Exception as e:
            ModernMessageBox.critical(self, "错误", f"导出出错: {str(e)}")

    def on_tab_changed(self, index):
        """懒加载：切换 tab 时只加载当前 tab 的数据"""
        if not hasattr(self, '_loaded_tabs') or not hasattr(self, 'month_edit'):
            return
        if index in self._loaded_tabs and self._current_month == self.month_edit.date().toString("yyyy-MM"):
            return
        self.load_current_tab(index)

    def load_current_tab(self, index):
        month = self.month_edit.date().toString("yyyy-MM")
        self._current_month = month
        if index == 0:
            self._load_drug_stats(month)
        elif index == 1:
            self._load_op_stats(month)
        elif index == 2:
            self._load_monthly_summary(month)
        elif index == 3:
            self._load_yearly_summary(self.month_edit.date().toString("yyyy"))
        self._loaded_tabs.add(index)

    def load_stats(self):
        """首次加载当前选中 tab"""
        self._loaded_tabs.clear()
        self.load_current_tab(self.tabs.currentIndex())

    def _load_drug_stats(self, month):
        res = api_client.get("/stats/drugs", params={"month": month})
        if res.status_code == 200 and res.json()['code'] == 200:
            result = res.json()['data']
            data_list = result.get('list', []) 
            summary = result.get('summary', {})
            
            # 获取盘点状态标记
            is_start_missing = result.get('isStartStockMissing', False)
            is_current_checked = result.get('isCurrentMonthChecked', True)
            
            if not is_current_checked:
                ModernMessageBox.warning(self, "盘点未完成", 
                                       f"{month} 月份尚未完成期末盘点，报表数据可能存在偏差。")
            
            self.drug_stats_tab.setColumnCount(13)
            self.drug_stats_tab.setHorizontalHeaderLabels([
                "药品", "规格", "单位",
                "期初数量", "期初金额", 
                "本月购进",  "购进单价", "购进金额",
                "本月使用", "使用金额",
                "期末理论", "期末实盘", "期末金额"
            ])
            
            self.drug_stats_tab.setRowCount(len(data_list) + 1) 
            
            for r, item in enumerate(data_list):
                self.drug_stats_tab.setItem(r, 0, QTableWidgetItem(str(item.get('drugName', ''))))
                self.drug_stats_tab.setItem(r, 1, QTableWidgetItem(str(item.get('spec', ''))))
                self.drug_stats_tab.setItem(r, 2, QTableWidgetItem(str(item.get('purchaseUnit', ''))))
                
                # 期初数据处理
                start_stock_item = QTableWidgetItem(str(item.get('startStock', 0)))
                start_amount_item = QTableWidgetItem(str(item.get('startAmount', 0)))
                
                if is_start_missing:
                    start_stock_item.setForeground(QColor(ERROR_COLOR))
                    start_amount_item.setForeground(QColor(ERROR_COLOR))
                    tip = "上个月未完成库存盘点，期初数据默认为0"
                    start_stock_item.setToolTip(tip)
                    start_amount_item.setToolTip(tip)
                
                self.drug_stats_tab.setItem(r, 3, start_stock_item)
                self.drug_stats_tab.setItem(r, 4, start_amount_item)
                
                self.drug_stats_tab.setItem(r, 5, QTableWidgetItem(str(item.get('purchaseQty', 0))))
                self.drug_stats_tab.setItem(r, 6, QTableWidgetItem(str(item.get('purchasePrice', 0))))
                self.drug_stats_tab.setItem(r, 7, QTableWidgetItem(str(item.get('purchaseAmount', 0))))
                self.drug_stats_tab.setItem(r, 8, QTableWidgetItem(str(item.get('useQty', 0))))
                self.drug_stats_tab.setItem(r, 9, QTableWidgetItem(str(item.get('useAmount', 0))))
                self.drug_stats_tab.setItem(r, 10, QTableWidgetItem(str(item.get('endTheoretical', 0))))
                
                end_actual = item.get('endActual')
                self.drug_stats_tab.setItem(r, 11, QTableWidgetItem(str(end_actual) if end_actual is not None else "-"))
                self.drug_stats_tab.setItem(r, 12, QTableWidgetItem(str(item.get('endAmount', 0))))
                
                self.drug_stats_tab.setRowHeight(r, 50)

            last_row = len(data_list)
            self.drug_stats_tab.setItem(last_row, 0, QTableWidgetItem("合计"))
            self.drug_stats_tab.setItem(last_row, 4, QTableWidgetItem(str(summary.get('totalStartAmount', 0))))
            self.drug_stats_tab.setItem(last_row, 7, QTableWidgetItem(str(summary.get('totalPurchaseAmount', 0))))
            self.drug_stats_tab.setItem(last_row, 9, QTableWidgetItem(str(summary.get('totalUseAmount', 0))))
            self.drug_stats_tab.setItem(last_row, 12, QTableWidgetItem(str(summary.get('totalEndAmount', 0))))
            self.drug_stats_tab.setRowHeight(last_row, 50)

    def _load_op_stats(self, month):
        res = api_client.get("/stats/operations", params={"month": month})
        if res.status_code == 200 and res.json()['code'] == 200:
            result = res.json()['data']
            summary = result.get('summary', {})
            daily_stats = result.get('dailyStats', [])
            
            if self.op_stats_tab.layout():
                QWidget().setLayout(self.op_stats_tab.layout()) 
            
            layout = QVBoxLayout(self.op_stats_tab)
            layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
            
            sum_card = ModernCard()
            sum_group = QHBoxLayout()
            sum_group.addWidget(ModernLabel(f"本月累计就诊: {summary.get('totalVisits', 0)} 人", size=FONT_SIZE_BASE, weight=FONT_WEIGHT_BOLD))
            sum_group.addWidget(ModernLabel(f"累计药品费用: {summary.get('totalCost', 0)} 元", size=FONT_SIZE_BASE, weight=FONT_WEIGHT_BOLD))
            sum_group.addWidget(ModernLabel(f"人均药品费用: {summary.get('avgCost', 0)} 元", size=FONT_SIZE_BASE, weight=FONT_WEIGHT_BOLD))
            sum_card.add_layout(sum_group)
            layout.addWidget(sum_card)
            
            daily_table = ModernTable()
            daily_table.setColumnCount(5)
            daily_table.setHorizontalHeaderLabels(["日期", "就诊人数", "药品费用", "人均费用", "诊治分类统计"])
            daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            daily_table.setRowCount(len(daily_stats))
            
            for r, day in enumerate(daily_stats):
                daily_table.setItem(r, 0, QTableWidgetItem(str(day.get('date', ''))))
                daily_table.setItem(r, 1, QTableWidgetItem(str(day.get('visits', 0))))
                daily_table.setItem(r, 2, QTableWidgetItem(str(day.get('totalCost', 0))))
                daily_table.setItem(r, 3, QTableWidgetItem(str(day.get('avgCost', 0))))
                daily_table.setItem(r, 4, QTableWidgetItem(str(day.get('diagnosisDetails', ''))))
                daily_table.setRowHeight(r, 50)
                
            layout.addWidget(daily_table)
            self.op_stats_tab.setLayout(layout)

    def _load_monthly_summary(self, month):
        res = api_client.get("/stats/monthly-summary", params={"month": month})
        if res.status_code == 200 and res.json()['code'] == 200:
            data = res.json()['data']
            rows = data.get('rows', [])
            leader_amt = data.get('leaderMedicineAmount', 0)
            init_stock = data.get('initialStockAmount', 0)
            purchase_amt = data.get('purchaseTotalAmount', 0)
            final_stock = data.get('finalStockAmount', 0)
            
            self.monthly_summary_tab.setRowCount(len(rows))
            self.monthly_summary_tab.clearSpans() # 清除旧的合并
            
            for r, item in enumerate(rows):
                self.monthly_summary_tab.setItem(r, 0, QTableWidgetItem(item.get('department')))
                self.monthly_summary_tab.setItem(r, 1, QTableWidgetItem(str(item.get('visitCount'))))
                self.monthly_summary_tab.setItem(r, 2, QTableWidgetItem(f"{item.get('prescriptionAmount'):.2f}"))
                self.monthly_summary_tab.setItem(r, 3, QTableWidgetItem(f"{item.get('traumaAmount'):.2f}"))
                
                # Global columns
                if r == 0:
                    self.monthly_summary_tab.setItem(r, 4, QTableWidgetItem(f"{leader_amt:.2f}"))
                    self.monthly_summary_tab.setItem(r, 5, QTableWidgetItem(f"{init_stock:.2f}"))
                    self.monthly_summary_tab.setItem(r, 6, QTableWidgetItem(f"{purchase_amt:.2f}"))
                    self.monthly_summary_tab.setItem(r, 7, QTableWidgetItem(f"{final_stock:.2f}"))
                else:
                    self.monthly_summary_tab.setItem(r, 4, QTableWidgetItem(""))
                    self.monthly_summary_tab.setItem(r, 5, QTableWidgetItem(""))
                    self.monthly_summary_tab.setItem(r, 6, QTableWidgetItem(""))
                    self.monthly_summary_tab.setItem(r, 7, QTableWidgetItem(""))

            # 设置对齐和合并
            if len(rows) > 0:
                for c in range(4, 8):
                    item = self.monthly_summary_tab.item(0, c)
                    if item:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                if len(rows) > 1:
                    self.monthly_summary_tab.setSpan(0, 4, len(rows), 1)
                    self.monthly_summary_tab.setSpan(0, 5, len(rows), 1)
                    self.monthly_summary_tab.setSpan(0, 6, len(rows), 1)
                    self.monthly_summary_tab.setSpan(0, 7, len(rows), 1)

            for r in range(len(rows)):
                self.monthly_summary_tab.setRowHeight(r, 50)

    def _load_yearly_summary(self, year):
        res = api_client.get("/stats/yearly-summary", params={"year": year})
        if res.status_code == 200 and res.json()['code'] == 200:
            data = res.json()['data']
            rows = data.get('rows', [])
            leader_amt = data.get('leaderMedicineAmount', 0)
            init_stock = data.get('initialStockAmount', 0)
            purchase_amt = data.get('purchaseTotalAmount', 0)
            final_stock = data.get('finalStockAmount', 0)
            is_last_missing = data.get('isLastYearStockMissing', False)
            missing_months = data.get('missingInventoryMonths', [])
            
            # 显示警告
            warnings = []
            if is_last_missing and init_stock == 0:
                warnings.append(f"警告：未找到 {int(year)-1} 年 12 月的盘点记录，期初库存金额可能不准确。")
            
            if missing_months:
                warnings.append(f"警告：以下月份尚未进行库存盘点，影响期末库存金额统计：{', '.join(missing_months)}")
            
            if warnings:
                msg = "\n".join(warnings)
                self.yearly_warning_label.setText(msg)
                self.yearly_warning_label.setVisible(True)
                # 同时也保留弹窗，双重提醒
                # ModernMessageBox.warning(self, "数据完整性警告", msg) 
            else:
                self.yearly_warning_label.setVisible(False)
            
            self.yearly_summary_tab.setRowCount(len(rows))
            self.yearly_summary_tab.clearSpans()
            
            for r, item in enumerate(rows):
                self.yearly_summary_tab.setItem(r, 0, QTableWidgetItem(item.get('department')))
                self.yearly_summary_tab.setItem(r, 1, QTableWidgetItem(str(item.get('visitCount'))))
                self.yearly_summary_tab.setItem(r, 2, QTableWidgetItem(f"{item.get('prescriptionAmount'):.2f}"))
                self.yearly_summary_tab.setItem(r, 3, QTableWidgetItem(f"{item.get('traumaAmount'):.2f}"))
                
                if r == 0:
                    leader_item = QTableWidgetItem(f"{leader_amt:.2f}")
                    
                    init_item = QTableWidgetItem(f"{init_stock:.2f}")
                    if is_last_missing and init_stock == 0:
                        init_item.setForeground(QColor(ERROR_COLOR))
                        init_item.setToolTip("上一年未盘点，数据缺失")
                    
                    purchase_item = QTableWidgetItem(f"{purchase_amt:.2f}")
                    
                    final_item = QTableWidgetItem(f"{final_stock:.2f}")
                    if missing_months:
                        final_item.setForeground(QColor(WARNING_COLOR))
                        final_item.setToolTip(f"缺失月份：{', '.join(missing_months)}")

                    self.yearly_summary_tab.setItem(r, 4, leader_item)
                    self.yearly_summary_tab.setItem(r, 5, init_item)
                    self.yearly_summary_tab.setItem(r, 6, purchase_item)
                    self.yearly_summary_tab.setItem(r, 7, final_item)
                else:
                    self.yearly_summary_tab.setItem(r, 4, QTableWidgetItem(""))
                    self.yearly_summary_tab.setItem(r, 5, QTableWidgetItem(""))
                    self.yearly_summary_tab.setItem(r, 6, QTableWidgetItem(""))
                    self.yearly_summary_tab.setItem(r, 7, QTableWidgetItem(""))

            if len(rows) > 0:
                for c in range(4, 8):
                    item = self.yearly_summary_tab.item(0, c)
                    if item:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                if len(rows) > 1:
                    self.yearly_summary_tab.setSpan(0, 4, len(rows), 1)
                    self.yearly_summary_tab.setSpan(0, 5, len(rows), 1)
                    self.yearly_summary_tab.setSpan(0, 6, len(rows), 1)
                    self.yearly_summary_tab.setSpan(0, 7, len(rows), 1)

            for r in range(len(rows)):
                self.yearly_summary_tab.setRowHeight(r, 50)
