from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                             QLineEdit, QDateEdit, QComboBox, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox, 
                             QDialog, QInputDialog, QHeaderView, QFrame, QAbstractItemView, QAbstractSpinBox)
from PyQt6.QtCore import QDate, Qt, QTimer, QEvent
from PyQt6.QtGui import QColor
from utils.api_client import api_client
from ui.style_constants import *
from ui.components import ModernButton, ModernInput, ModernLabel, ModernCard, ModernMessageBox, PaginationControl, SmartDateEdit, DepartmentFilterGroup, SearchableComboBox, StatusFilterGroup, DiagnosisSelectionDialog, DrugSelectionDialog, ModernTable, ModernInputDialog

class VisitCreateView(QWidget):
    def __init__(self):
        super().__init__()
        self.drugs = [] # 缓存药品列表
        self.diagnosis_types = [] # 缓存诊断类型
        self.selected_drugs = [] # 已选药品
        
        self.drug_search_timer = QTimer(self)
        self.drug_search_timer.setSingleShot(True)
        self.drug_search_timer.setInterval(300)
        self.drug_search_timer.timeout.connect(self.perform_drug_search)
        
        self.initUI()
        
        self.load_data()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        layout.setSpacing(SPACING_LG_INT)
        
        # 主卡片
        main_card = ModernCard()
        
        title = ModernLabel("填写患者就诊信息", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800)
        main_card.add_widget(title)
        
        # 表单区域
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.name_input = ModernInput(placeholder="请输入患者姓名")
        self.name_input.setFixedWidth(120)
        
        self.gender_input = QComboBox()
        self.gender_input.addItems(["男", "女"])
        self.gender_input.setFixedHeight(40)
        self.gender_input.setFixedWidth(60)
        self.style_combobox(self.gender_input)
        
        self.age_input = ModernInput(placeholder="年龄")
        self.age_input.setFixedWidth(60)
        self.age_input.setValidator(None) # 可以加数字校验

        self.department_input = QComboBox()
        self.department_input.addItems(["本厂","外包","领导拿药"])
        self.department_input.setFixedHeight(40)
        self.department_input.setFixedWidth(100)
        self.style_combobox(self.department_input)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setCalendarPopup(True)
        self.date_input.setFixedHeight(40)
        self.date_input.setFixedWidth(140)
        self.style_dateedit(self.date_input)
        
        # 诊断类型 (支持新增和删除，支持自定义，支持搜索)
        diag_layout = QHBoxLayout()
        diag_layout.setSpacing(10)
        
        # 诊断输入框，点击弹出搜索窗口
        self.diag_search_input = SearchableComboBox(placeholder="搜索/选择诊断...")
        self.diag_search_input.setFixedWidth(250)
        self.diag_search_input.item_selected.connect(self.handle_diagnosis_selection)
        # Handle "Custom" if selected or typed
        
        self.selected_diag_id = None
        self.selected_diag_name = None
        
        self.custom_diag_input = ModernInput(placeholder="请输入自定义诊断")
        self.custom_diag_input.setVisible(False)
        
        self.cancel_custom_btn = ModernButton("×", variant="secondary")
        self.cancel_custom_btn.setFixedSize(40, 40)
        self.cancel_custom_btn.setToolTip("取消自定义，返回选择")
        self.cancel_custom_btn.clicked.connect(self.cancel_custom_diagnosis)
        self.cancel_custom_btn.setVisible(False)
        
        add_diag_btn = ModernButton("+", variant="outline")
        add_diag_btn.setFixedSize(40, 40)
        add_diag_btn.setToolTip("新增诊断类型")
        add_diag_btn.clicked.connect(self.add_diagnosis)

        edit_diag_btn = ModernButton("改", variant="outline")
        edit_diag_btn.setFixedSize(46, 40)
        edit_diag_btn.setToolTip("修改诊断分类名称")
        edit_diag_btn.clicked.connect(self.edit_diagnosis)
        
        del_diag_btn = ModernButton("-", variant="danger")
        del_diag_btn.setFixedSize(40, 40)
        del_diag_btn.setToolTip("删除当前选中的诊断类型")
        del_diag_btn.clicked.connect(self.delete_diagnosis)
        
        diag_layout.addWidget(self.diag_search_input)
        diag_layout.addWidget(self.custom_diag_input)
        diag_layout.addWidget(self.cancel_custom_btn)
        diag_layout.addWidget(add_diag_btn)
        diag_layout.addWidget(edit_diag_btn)
        diag_layout.addWidget(del_diag_btn)
        
        row_1 = QHBoxLayout()
        row_1.addWidget(ModernLabel("患者姓名:"))
        row_1.addWidget(self.name_input)
        row_1.addSpacing(15)
        row_1.addWidget(ModernLabel("性别:"))
        row_1.addWidget(self.gender_input)
        row_1.addSpacing(15)
        row_1.addWidget(ModernLabel("年龄:"))
        row_1.addWidget(self.age_input)
        row_1.addSpacing(15)
        row_1.addWidget(ModernLabel("部门:"))
        row_1.addWidget(self.department_input)
        row_1.addStretch()
        
        row_2 = QHBoxLayout()
        row_2.addWidget(ModernLabel("就诊日期:"))
        row_2.addWidget(self.date_input)
        row_2.addSpacing(15)
        row_2.addWidget(ModernLabel("临床诊断:"))
        row_2.addLayout(diag_layout)
        row_2.addStretch()
        
        form_layout.addRow(row_1)
        form_layout.addRow(row_2)
        
        main_card.add_layout(form_layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {GRAY_200}; max-height: 1px; margin: 10px 0;")
        main_card.add_widget(line)
        
        # 药品选择区域
        main_card.add_widget(ModernLabel("处方药品:", weight=FONT_WEIGHT_BOLD, color=GRAY_700))
        
        drug_control_layout = QHBoxLayout()
        drug_control_layout.setSpacing(10)
        
        # 1. 药品搜索框 (SearchableComboBox)
        self.drug_search_input = SearchableComboBox(placeholder="输入名称搜索/选择药品...")
        self.drug_search_input.item_selected.connect(self.handle_drug_selection)
        self.drug_search_input.text_changed.connect(self.on_drug_search_text_changed)
        
        self.selected_drug_id = None
        self.selected_drug_name = None
        
        self.quantity_input = ModernInput(placeholder="数量")
        self.quantity_input.setFixedWidth(120)
        
        self.unit_input = ModernInput(placeholder="单位")
        self.unit_input.setFixedWidth(60)
        self.unit_input.setReadOnly(True)
        
        add_drug_btn = ModernButton("添加药品", variant="secondary")
        add_drug_btn.clicked.connect(self.add_drug_to_list)
        
        drug_control_layout.addWidget(self.drug_search_input, 1)
        drug_control_layout.addWidget(self.quantity_input)
        drug_control_layout.addWidget(self.unit_input)
        drug_control_layout.addWidget(add_drug_btn)
        
        main_card.add_layout(drug_control_layout)
        
        # 已选药品列表
        self.drug_table = ModernTable()
        self.drug_table.setColumnCount(5)
        self.drug_table.setHorizontalHeaderLabels(["ID", "药品名称", "数量", "单位", "操作"])
        self.drug_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        main_card.add_widget(self.drug_table)
        
        # 提交按钮
        submit_btn = ModernButton("提交就诊记录", variant="primary")
        submit_btn.clicked.connect(self.submit_visit)
        main_card.add_widget(submit_btn)
        
        layout.addWidget(main_card)
        self.setLayout(layout)
        
        self.installEventFilter(self)
        self.setup_keyboard_navigation()

    def setup_keyboard_navigation(self):
        # 1. 姓名 -> 性别
        self.name_input.returnPressed.connect(self.focus_gender)
        
        # 2. 性别 -> 年龄
        self.gender_input.activated.connect(self.focus_age)
        
        # 3. 年龄 -> 部门
        self.age_input.returnPressed.connect(self.focus_department)
        
        # 4. 部门 -> 就诊日期
        self.department_input.activated.connect(self.focus_date)
        
        # 5. 就诊日期 -> 临床诊断 (在 eventFilter 中处理回车)
        self.date_input.installEventFilter(self)
        
        # 6. 自定义诊断 -> 药品搜索
        self.custom_diag_input.returnPressed.connect(self.focus_drug_search)
        
        # 7. 数量 -> 添加药品
        self.quantity_input.returnPressed.connect(self.add_drug_to_list)

    def focus_department(self):
        self.department_input.setFocus()
        self.department_input.showPopup()

    def focus_gender(self):
        self.gender_input.setFocus()
        self.gender_input.showPopup()

    def focus_age(self):
        self.age_input.setFocus()

    def focus_date(self):
        self.date_input.setFocus()
        # 尝试展开日历。对于 QDateEdit，showPopup 是受保护的。
        # 但 SmartDateEdit 继承自 QDateEdit，我们可以添加一个 public 方法。
        # 或者发送 F4 键事件
        # from PyQt6.QtGui import QKeyEvent
        # event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier)
        # QApplication.sendEvent(self.date_input, event)
        # 暂时只聚焦，让用户决定是否展开（用户说默认是今天，再回车就跳过）
        # 如果必须展开，可以在 SmartDateEdit 加方法。
        # 鉴于 SmartDateEdit 是我们自己定义的，去加一个 open_calendar 方法最好。
        if hasattr(self.date_input, 'open_calendar'):
            self.date_input.open_calendar()

    def focus_diagnosis(self):
        self.diag_search_input.input.setFocus()
        self.diag_search_input.show_popup()

    def focus_drug_search(self):
        self.drug_search_input.input.setFocus()
        self.drug_search_input.show_popup()

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
            QComboBox:hover {{
                border-color: {GRAY_400};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {GRAY_500};
                margin-right: 5px;
            }}
        """)

    def style_dateedit(self, date_edit):
        date_edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
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
            QDateEdit:hover {{
                border-color: {GRAY_400};
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {GRAY_500};
                margin-right: 5px;
            }}
            QCalendarWidget QWidget {{
                color: {BLACK};
            }}
            QCalendarWidget QToolButton {{
                color: {BLACK};
            }}
            QDateEdit::up-button, QDateEdit::down-button {{
                width: 0px;
                border: none;
            }}
        """)

    def load_data(self):
        # 初始化加载一次数据
        # 预加载一些药品数据，防止点击搜索框时列表为空
        self.perform_drug_search() 
        # 加载诊断类型
        self.refresh_diagnosis()

    def refresh_diagnosis(self):
        res = api_client.get("/diagnosis-types")
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.diagnosis_types = data['data']
                # 始终添加 "自定义诊断" 到首位
                custom_diag = {"id": "CUSTOM", "name": "--- 自定义诊断 ---"}
                # 避免重复添加
                if not any(d.get('id') == "CUSTOM" for d in self.diagnosis_types):
                     self.diagnosis_types.insert(0, custom_diag)
                
                # 更新下拉框数据
                self.diag_search_input.set_data(self.diagnosis_types, text_key='name')

    def handle_diagnosis_selection(self, selected):
        if not selected:
            return
            
        data = selected.get('id')
        name = selected.get('name')
        
        if data == "CUSTOM":
            self.selected_diag_id = "CUSTOM"
            self.diag_search_input.setVisible(False)
            self.custom_diag_input.setVisible(True)
            self.cancel_custom_btn.setVisible(True)
            self.custom_diag_input.setFocus()
        else:
            self.selected_diag_id = data
            self.selected_diag_name = name
            self.diag_search_input.setVisible(True)
            self.custom_diag_input.setVisible(False)
            self.cancel_custom_btn.setVisible(False)
            
            # 选中常规诊断后，跳转到药品搜索
            self.focus_drug_search()

    def on_drug_search_text_changed(self, text):
        self.drug_search_timer.start()

    def perform_drug_search(self):
        keyword = self.drug_search_input.input.text()
        res = api_client.get("/drugs", params={"keyword": keyword, "size": 20})
        if res.status_code == 200:
             data = res.json()
             if data['code'] == 200:
                 drugs = data['data']['records']
                 for d in drugs:
                     stock = d.get('stockQuantity', 0)
                     d['display_name'] = f"{d['name']} ({d['spec']}) - 库存:{stock}"
                 
                 self.drug_search_input.set_data(drugs, text_key='display_name', keep_text=True)

    def handle_drug_selection(self, drug):
        if not drug: return
        self.selected_drug_id = drug['id']
        self.selected_drug_name = drug['name']
        self.unit_input.setText(drug['unit'])
        self.quantity_input.setFocus()

    def eventFilter(self, source, event):
        # 处理 date_input 的回车事件
        if source == self.date_input and event.type() == QEvent.Type.KeyPress:
             if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                 self.focus_diagnosis()
                 return True

        if event.type() == QEvent.Type.MouseButtonPress:
            click_pos = event.pos()
            if source != self:
                click_pos = source.mapTo(self, click_pos)
                
        return super().eventFilter(source, event)

    def cancel_custom_diagnosis(self):
        self.custom_diag_input.clear()
        self.custom_diag_input.setVisible(False)
        self.cancel_custom_btn.setVisible(False)
        self.diag_search_input.setVisible(True)
        self.diag_search_input.clear()
        self.selected_diag_id = None

    def add_diagnosis(self):
        dlg = ModernInputDialog(self, "新增诊断", "请输入诊断名称:")
        if dlg.exec() == QDialog.DialogCode.Accepted and (name := dlg.get_text()):

            res = api_client.post("/diagnosis-types", {"name": name, "remark": "由医师新增"})
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "添加成功")
                self.refresh_diagnosis()
                # 用户要求添加成功后不要自动同步到输入框
                # self.selected_diag_id = res.json()['data']
                # self.diag_search_input.setText(name)
                # self.selected_diag_name = name
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

    def edit_diagnosis(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改诊断分类")
        dialog.setFixedSize(300, 450) # 稍微增加高度以容纳搜索框
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        
        # 添加搜索框
        search_input = ModernInput(placeholder="搜索诊断分类...")
        layout.addWidget(search_input)
        
        list_widget = ModernTable()
        list_widget.setColumnCount(2)
        list_widget.setHorizontalHeaderLabels(["ID", "名称"])
        list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        list_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        list_widget.setRowCount(len(self.diagnosis_types))
        for r, diag in enumerate(self.diagnosis_types):
            list_widget.setItem(r, 0, QTableWidgetItem(str(diag['id'])))
            list_widget.setItem(r, 1, QTableWidgetItem(diag['name']))
            list_widget.item(r, 0).setData(Qt.ItemDataRole.UserRole, diag)
            
        layout.addWidget(list_widget)
        
        # 搜索过滤功能
        def filter_items(text):
            for i in range(list_widget.rowCount()):
                item = list_widget.item(i, 1) # 名称在第二列
                if not text or text.lower() in item.text().lower():
                    list_widget.setRowHidden(i, False)
                else:
                    list_widget.setRowHidden(i, True)
        
        search_input.textChanged.connect(filter_items)
        
        btn_layout = QHBoxLayout()
        edit_btn = ModernButton("修改选中", variant="primary")
        cancel_btn = ModernButton("取消", variant="secondary")
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def confirm_edit():
            selected_items = list_widget.selectedItems()
            if not selected_items:
                ModernMessageBox.warning(dialog, "提示", "请先选择要修改的分类")
                return
                
            row = selected_items[0].row()
            diag = list_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            dlg2 = ModernInputDialog(dialog, "修改名称", f"请输入"{diag['name']}"的新名称:", default_text=diag['name'])
            if dlg2.exec() == QDialog.DialogCode.Accepted and (new_name := dlg2.get_text()) and new_name != diag['name']:
                res = api_client.put(f"/diagnosis-types/{diag['id']}", {"name": new_name})
                if res.status_code == 200 and res.json()['code'] == 200:
                    ModernMessageBox.information(dialog, "成功", "修改成功")
                    self.refresh_diagnosis()
                    dialog.accept()
                    # 更新当前输入框（如果正好选中的是这个）
                    if self.selected_diag_id == diag['id']:
                        self.selected_diag_name = new_name
                        self.diag_search_input.setText(new_name)
                else:
                    ModernMessageBox.critical(dialog, "失败", f"操作失败: {res.json().get('message')}")
        
        edit_btn.clicked.connect(confirm_edit)
        dialog.exec()

    def delete_diagnosis(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("删除诊断分类")
        dialog.setFixedSize(300, 450) # 稍微增加高度以容纳搜索框
        dialog.setStyleSheet(f"background-color: {WHITE};")
        
        layout = QVBoxLayout(dialog)
        
        # 添加搜索框
        search_input = ModernInput(placeholder="搜索诊断分类...")
        layout.addWidget(search_input)
        
        list_widget = ModernTable()
        list_widget.setColumnCount(2)
        list_widget.setHorizontalHeaderLabels(["ID", "名称"])
        list_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        list_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        list_widget.setRowCount(len(self.diagnosis_types))
        for r, diag in enumerate(self.diagnosis_types):
            list_widget.setItem(r, 0, QTableWidgetItem(str(diag['id'])))
            list_widget.setItem(r, 1, QTableWidgetItem(diag['name']))
            list_widget.item(r, 0).setData(Qt.ItemDataRole.UserRole, diag)
            
        layout.addWidget(list_widget)
        
        # 搜索过滤功能
        def filter_items(text):
            for i in range(list_widget.rowCount()):
                item = list_widget.item(i, 1) # 名称在第二列
                if not text or text.lower() in item.text().lower():
                    list_widget.setRowHidden(i, False)
                else:
                    list_widget.setRowHidden(i, True)
        
        search_input.textChanged.connect(filter_items)
        
        btn_layout = QHBoxLayout()
        del_btn = ModernButton("删除选中", variant="danger")
        cancel_btn = ModernButton("取消", variant="secondary")
        
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        cancel_btn.clicked.connect(dialog.reject)
        
        def confirm_delete():
            selected_items = list_widget.selectedItems()
            if not selected_items:
                ModernMessageBox.warning(dialog, "提示", "请先选择要删除的分类")
                return
                
            row = selected_items[0].row()
            diag = list_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
            
            reply = ModernMessageBox.question(dialog, "确认", f"确定要删除诊断分类“{diag['name']}”吗？\n注意：如果已有就诊记录使用了该分类，可能会导致删除失败。",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                res = api_client.delete(f"/diagnosis-types/{diag['id']}")
                if res.status_code == 200 and res.json()['code'] == 200:
                    ModernMessageBox.information(dialog, "成功", "删除成功")
                    self.refresh_diagnosis()
                    dialog.accept()
                else:
                    ModernMessageBox.critical(dialog, "失败", f"操作失败: {res.json().get('message')}")
        
        del_btn.clicked.connect(confirm_delete)
        dialog.exec()

    def add_drug_to_list(self):
        drug_id = self.selected_drug_id
        drug_name = self.selected_drug_name
        qty = self.quantity_input.text()
        unit = self.unit_input.text()

        if not drug_id:
            ModernMessageBox.warning(self, "提示", "请先选择药品")
            return
        
        if not qty.isdigit() or int(qty) <= 0:
            ModernMessageBox.warning(self, "提示", "请输入有效的数量")
            return
        for i in self.selected_drugs:
            if drug_id == i['drugId']:
                i["quantity"] = i["quantity"] + int(qty)
                self.refresh_drug_table()
                self.quantity_input.clear()
                self.drug_search_input.clear()
                self.unit_input.clear()
                self.selected_drug_id = None
                self.selected_drug_name = None
                return
        self.selected_drugs.append({
            "drugId": drug_id,
            "name": drug_name,
            "quantity": int(qty),
            "unit": unit
        })
        self.refresh_drug_table()
        self.quantity_input.clear()
        self.drug_search_input.clear()
        self.unit_input.clear()
        self.selected_drug_id = None
        self.selected_drug_name = None
        
        # 添加完成后，聚焦到药品搜索框，以便继续添加
        self.drug_search_input.input.setFocus()
        # 注意：这里不自动弹出，避免用户想提交时被打断。
        # 如果用户想继续添加，按下回车或点击即可（需确保 drug_search_input 回车能触发）
        # drug_search_input 是 ModernInput (QLineEdit)，只读。
        # 我们需要在 eventFilter 或 setup_keyboard_navigation 中处理 drug_search_input 的回车。
        # 或者因为它是只读的，回车可能不触发 editingFinished？
        # returnPressed 信号通常在按下回车时触发。
        # 让我们检查 drug_search_input 的回车是否被处理。
        
    def refresh_drug_table(self):
        self.drug_table.setRowCount(len(self.selected_drugs))
        for r, item in enumerate(self.selected_drugs):
            self.drug_table.setItem(r, 0, QTableWidgetItem(str(item['drugId'])))
            self.drug_table.setItem(r, 1, QTableWidgetItem(item['name']))
            self.drug_table.setItem(r, 2, QTableWidgetItem(str(item['quantity'])))
            self.drug_table.setItem(r, 3, QTableWidgetItem(item.get('unit', '')))
            
            del_btn = ModernButton("删除", variant="danger")
            del_btn.setFixedSize(60, 40)
            del_btn.setStyleSheet(del_btn.styleSheet() + f"font-size: {FONT_SIZE_XS}; padding: 0;")
            del_btn.clicked.connect(lambda _, row=r: self.remove_drug(row))
            
            btn_container = QWidget()
            layout = QHBoxLayout(btn_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(del_btn)
            
            self.drug_table.setCellWidget(r, 4, btn_container)
            self.drug_table.setRowHeight(r,60)
    def remove_drug(self, row):
        self.selected_drugs.pop(row)
        self.refresh_drug_table()

    def submit_visit(self):
        if not self.name_input.text() or not self.age_input.text():
            ModernMessageBox.warning(self, "提示", "请填写完整患者信息")
            return
        
        if not self.selected_drugs:
            ModernMessageBox.warning(self, "提示", "请至少添加一种药品")
            return
            
        # 诊断检查
        diag_id = self.selected_diag_id
        custom_diag = None
        
        if diag_id == "CUSTOM":
            custom_diag = self.custom_diag_input.text().strip()
            if not custom_diag:
                ModernMessageBox.warning(self, "提示", "请输入自定义诊断内容")
                return
            diag_id = None # 自定义时不传 ID
        elif diag_id is None:
             ModernMessageBox.warning(self, "提示", "请选择临床诊断")
             return

        data = {
            "patientName": self.name_input.text(),
            "gender": self.gender_input.currentText(),
            "age": int(self.age_input.text()),
            "department": self.department_input.currentText(),
            "visitDate": self.date_input.date().toString("yyyy-MM-dd"),
            "diagnosisId": diag_id,
            "customDiagnosis": custom_diag,
            "drugs": [{"drugId": d['drugId'], "quantity": d['quantity']} for d in self.selected_drugs]
        }
        
        res = api_client.post("/visits", data)
        if res.status_code == 200 and res.json()['code'] == 200:
            ModernMessageBox.information(self, "成功", "就诊记录已提交，等待药师发药")
            # 清空表单
            self.name_input.clear()
            self.age_input.clear()
            self.selected_drugs = []
            self.refresh_drug_table()
        else:
            ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message', '未知错误')}")

class VisitHistoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.diagnosis_types = []
        self.selected_diag_id = None
        self.initUI()
        self.load_data()
        # 定时刷新，及时感知药师发药/退回的状态变更
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(8000)

    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)

    def _auto_refresh(self):
        if self.isVisible():
            self.load_data()

    def reset_search(self):
        self.search_input.clear()
        self.start_date.setDate(QDate(2000, 1, 1))
        self.end_date.setDate(QDate(2000, 1, 1))
        
        self.selected_diag_id = None
        self.diag_search_input.clear()
        self.custom_diag_input.clear()
        self.custom_diag_input.setVisible(False)
        
        self.dept_filter.reset_selection()
        self.status_filter.reset_selection()
        self.on_search()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_LG_INT)
        
        # 顶部操作栏
        top_card = ModernCard()
        top_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        top_layout = QVBoxLayout()
        top_layout.setSpacing(10)
        
        # 第一行：标题 + 基础筛选
        row1 = QHBoxLayout()
        
        row1.addWidget(ModernLabel("我的就诊记录", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800))
        # row1.addStretch() # 移除这个，改用 spacing 或 比例
        row1.addSpacing(40) 
        
        self.search_input = ModernInput(placeholder="搜索患者姓名...")
        self.search_input.setFixedWidth(150)
        
        self.start_date = SmartDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumDate(QDate(2000, 1, 1))
        self.start_date.setDate(QDate(2000, 1, 1))
        self.start_date.setSpecialValueText(" ")
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedWidth(140)
        
        self.end_date = SmartDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setMinimumDate(QDate(2000, 1, 1))
        self.end_date.setDate(QDate(2000, 1, 1))
        self.end_date.setSpecialValueText(" ")
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
        row1.addSpacing(10)
        row1.addWidget(search_btn)
        row1.addWidget(clear_btn)
        row1.addStretch() # 让内容靠左
        
        top_layout.addLayout(row1)
        
        # 第二行：高级筛选
        row2 = QHBoxLayout()
        
        self.diag_search_input = ModernInput(placeholder="点击选择诊断...")
        self.diag_search_input.setReadOnly(True)
        self.diag_search_input.setFixedWidth(200)
        self.diag_search_input.installEventFilter(self)
        
        self.custom_diag_input = ModernInput(placeholder="输入自定义诊断...")
        self.custom_diag_input.setFixedWidth(200)
        self.custom_diag_input.setVisible(False)
        
        self.load_diagnosis_types()
        
        self.dept_filter = DepartmentFilterGroup()
        self.dept_filter.department_changed.connect(self.on_search)
        
        # 为了对齐第一行的输入框起始位置
        # 第一行: Title(width) + 40 + Label("患者姓名:")(width) + Input
        # Title width不定。
        # 简单的做法是让 row2 也左对齐，并尝试与上面对齐。
        # 由于 Title 存在，row2 需要缩进。
        # 我们可以用 grid layout 替代，或者手动加 spacing。
        # Title 大概 100-150px? 
        # 让我们简单地加一个 spacing 占位，或者直接左对齐。
        # 用户说“整体向左移动多一点”，如果之前是靠右（addStretch在左），现在改为靠左（addStretch在右），那就符合需求。
        # 之前 row2.addStretch(); row2.addWidget(...)
        
        # row2.addSpacing(180) # 估算标题宽度 + 间距
        # 不估算，直接左对齐，稍微缩进一点以区分层级，或者不缩进。
        
        row2.addWidget(ModernLabel("诊断筛选:"))
        row2.addWidget(self.diag_search_input)
        row2.addWidget(self.custom_diag_input)
        row2.addSpacing(40)
        row2.addWidget(ModernLabel("部门筛选:"))
        row2.addWidget(self.dept_filter)
        row2.addStretch() # 靠左
        
        top_layout.addLayout(row2)

        # 第三行：状态筛选
        row3 = QHBoxLayout()
        self.status_filter = StatusFilterGroup()
        self.status_filter.status_changed.connect(self.on_search)
        
        row3.addWidget(ModernLabel("状态筛选:"))
        row3.addWidget(self.status_filter)
        row3.addStretch()
        
        top_layout.addLayout(row3)
        
        top_card.add_layout(top_layout)
        layout.addWidget(top_card)
        
        # ... (rest of initUI)
        
        # 表格
        table_card = ModernCard()
        table_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        self.table = ModernTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "患者", "日期", "状态", "诊断", "退回原因", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 120)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 80)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 250)
        
        table_card.add_widget(self.table)
        
        self.pagination = PaginationControl()
        self.pagination.page_changed.connect(lambda: self.load_data())
        self.pagination.size_changed.connect(lambda: self.load_data())
        table_card.add_widget(self.pagination)
        
        layout.addWidget(table_card)
        
        self.setLayout(layout)

    def style_dateedit(self, date_edit):
        # 复用样式逻辑
        date_edit.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
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
                width: 25px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }}
            QDateEdit::drop-down:hover {{
                background-color: {GRAY_100};
                border-top-right-radius: {RADIUS_BASE};
                border-bottom-right-radius: {RADIUS_BASE};
            }}
            QDateEdit:hover {{
                border-color: {GRAY_400};
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {GRAY_600};
                width: 0;
                height: 0;
                margin-right: 5px;
            }}
            QCalendarWidget QWidget {{
                color: {BLACK};
            }}
            QCalendarWidget QToolButton {{
                color: {BLACK};
            }}
            QDateEdit::up-button, QDateEdit::down-button {{
                width: 0px;
                border: none;
            }}
        """)

    def load_diagnosis_types(self):
        res = api_client.get("/diagnosis-types")
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 200:
                self.diagnosis_types = data['data']

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
            "page": page,
            "size": size,
            "keyword": self.search_input.text(),
            "startDate": start_str,
            "endDate": end_str,
            "diagnosisId": diag_id,
            "customDiagnosis": custom_diag,
            "department": self.dept_filter.selected_dept
        }
        
        if self.status_filter.selected_status:
            params["status"] = self.status_filter.selected_status
            
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
            status = item.get('status')
            diagnosis_id = item.get('diagnosisId')
            diagnosis_name = item.get('diagnosisName')
            return_reason = item.get('returnReason')
            
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
            
            # 状态颜色
            if status == 'COMPLETED':
                status_item.setForeground(QColor(SUCCESS_COLOR))
            elif status == 'RETURNED':
                status_item.setForeground(QColor(ERROR_COLOR))
            elif status == 'SUBMITTED':
                status_item.setForeground(QColor(PRIMARY_COLOR))
            elif status == 'CANCELED':
                status_item.setForeground(QColor(ERROR_COLOR))
                
            self.table.setItem(r, 3, status_item)
            
            self.table.setItem(r, 4, QTableWidgetItem(diagnosis_name if diagnosis_name else str(diagnosis_id) if diagnosis_id else ""))
            self.table.setItem(r, 5, QTableWidgetItem(return_reason or ""))
            
            btn_container = QWidget()
            layout = QHBoxLayout(btn_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            detail_btn = ModernButton("详情", variant="secondary")
            detail_btn.setFixedSize(60, 32)
            detail_btn.setStyleSheet(detail_btn.styleSheet() + f"QPushButton {{ font-size: {FONT_SIZE_BASE}; padding: 0; }}")
            detail_btn.clicked.connect(lambda _, item=item: self.show_detail(item))
            layout.addWidget(detail_btn)
            
            if status == 'RETURNED':
                btn = ModernButton("修改重提", variant="warning")
                btn.setFixedSize(80, 32)
                # 追加样式规则以覆盖默认设置
                btn.setStyleSheet(btn.styleSheet() + f"QPushButton {{ font-size: {FONT_SIZE_BASE}; padding: 0; }}")
                btn.clicked.connect(lambda _, vid=visit_id: self.edit_visit(vid))
                layout.addWidget(btn)
            
            # 只有待发药和已退回状态可以取消
            if status in ['SUBMITTED', 'RETURNED']:
                cancel_btn = ModernButton("取消", variant="danger")
                cancel_btn.setFixedSize(60, 32)
                cancel_btn.setStyleSheet(cancel_btn.styleSheet() + f"QPushButton {{ font-size: {FONT_SIZE_BASE}; padding: 0; }}")
                cancel_btn.clicked.connect(lambda _, vid=visit_id: self.cancel_visit(vid))
                layout.addWidget(cancel_btn)
                
            self.table.setCellWidget(r, 6, btn_container)
            
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

    def cancel_visit(self, visit_id):
        reply = ModernMessageBox.question(self, "确认", "确定要取消该就诊记录吗？此操作不可恢复！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            res = api_client.post(f"/visits/{visit_id}/cancel")
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(self, "成功", "就诊记录已取消")
                self.load_data()
            else:
                ModernMessageBox.critical(self, "失败", f"操作失败: {res.json().get('message')}")

    def show_detail(self, visit_item):
        dialog = QDialog(self)
        dialog.setWindowTitle("就诊详情")
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
        info_layout.addRow(ModernLabel("诊断信息:", weight=FONT_WEIGHT_BOLD), ModernLabel(visit_item.get('diagnosisName') or ""))
        
        if visit_item.get('returnReason'):
            reason_label = ModernLabel(visit_item.get('returnReason'), color=ERROR_COLOR)
            info_layout.addRow(ModernLabel("退回原因:", weight=FONT_WEIGHT_BOLD, color=ERROR_COLOR), reason_label)
        
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

    def edit_visit(self, visit_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改并重新提交就诊记录")
        dialog.setFixedSize(700, 800)
        dialog.setStyleSheet(f"background-color: {GRAY_50};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        edit_view = VisitCreateView()
        # 移除 edit_view 自身的 margin，因为 dialog 已经有了
        edit_view.layout().setContentsMargins(0,0,0,0)
        
        original_submit = edit_view.submit_visit
        
        def update_submit():
            if not edit_view.name_input.text() or not edit_view.age_input.text():
                ModernMessageBox.warning(dialog, "提示", "请填写完整患者信息")
                return
            
            if not edit_view.selected_drugs:
                ModernMessageBox.warning(dialog, "提示", "请至少添加一种药品")
                return
            
            diag_id = edit_view.selected_diag_id
            if diag_id == "CUSTOM":
                custom_diag = edit_view.custom_diag_input.text().strip()
                if not custom_diag:
                    ModernMessageBox.warning(dialog, "提示", "请输入自定义诊断内容")
                    return
                diag_id = None
            elif diag_id is None:
                 ModernMessageBox.warning(dialog, "提示", "请选择临床诊断")
                 return
                
            data = {
                "patientName": edit_view.name_input.text(),
                "gender": edit_view.gender_input.currentText(),
                "age": int(edit_view.age_input.text()),
                "department": edit_view.department_input.currentText(),
                "visitDate": edit_view.date_input.date().toString("yyyy-MM-dd"),
                "diagnosisId": diag_id,
                "drugs": [{"drugId": d['drugId'], "quantity": d['quantity']} for d in edit_view.selected_drugs]
            }
            
            res = api_client.put(f"/visits/{visit_id}", data)
            if res.status_code == 200 and res.json()['code'] == 200:
                ModernMessageBox.information(dialog, "成功", "已修改并重新提交")
                dialog.accept()
                self.load_data()
            else:
                ModernMessageBox.critical(dialog, "失败", f"操作失败: {res.json().get('message')}")
        
        submit_btn = edit_view.findChildren(QPushButton)[-1] 
        submit_btn.clicked.disconnect()
        submit_btn.clicked.connect(update_submit)
        submit_btn.setText("确认修改并提交")
        
        record = next((r for r in self.records if r.get('id') == visit_id), None)
        if record:
            edit_view.name_input.setText(record.get('patientName', ''))
            edit_view.age_input.setText(str(record.get('age', '')))
            edit_view.department_input.setCurrentText(record.get('department', ''))
            edit_view.gender_input.setCurrentText(record.get('gender', ''))
            if record.get('visitDate'):
                edit_view.date_input.setDate(QDate.fromString(record['visitDate'], "yyyy-MM-dd"))
            
            diag_id = record.get('diagnosisId')
            diag_name = record.get('diagnosisName')
            
            if diag_id:
                # 模拟选中诊断
                edit_view.selected_diag_id = diag_id
                edit_view.selected_diag_name = diag_name
                edit_view.diag_search_input.setText(diag_name)
            
            if 'drugs' in record:
                for d in record['drugs']:
                    # 优先使用记录中的药品名称（后端通常已返回），如果为空则尝试从缓存中查找
                    name = d.get('drugName')
                    spec = d.get('spec', '')
                    
                    if name:
                        drug_name = f"{name} ({spec})"
                    else:
                        drug_info = next((item for item in edit_view.drugs if item['id'] == d['drugId']), None)
                        drug_name = f"{drug_info['name']} ({drug_info['spec']})" if drug_info else f"Drug ID: {d['drugId']}"
                    
                    edit_view.selected_drugs.append({
                        "drugId": d['drugId'],
                        "name": drug_name,
                        "quantity": d['quantity']
                    })
                edit_view.refresh_drug_table()

        layout.addWidget(edit_view)
        dialog.exec()

class DrugQueryView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()
        QTimer.singleShot(0, self._connect_stock_signal)

    def _connect_stock_signal(self):
        mw = self.window()
        if hasattr(mw, 'stock_changed'):
            mw.stock_changed.connect(self.load_data)

    def showEvent(self, event):
        self.load_data()
        super().showEvent(event)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING_LG_INT)

        # 顶部操作栏
        top_card = ModernCard()
        top_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        top = QHBoxLayout()
        
        top.addWidget(ModernLabel("药品查询", size=FONT_SIZE_LG, weight=FONT_WEIGHT_BOLD, color=GRAY_800))
        top.addStretch()
        
        self.search_input = ModernInput(placeholder="搜索药品名称...")
        search_btn = ModernButton("查询", variant="primary")
        search_btn.clicked.connect(self.on_search)
        
        top.addWidget(self.search_input)
        top.addWidget(search_btn)
        
        top_card.add_layout(top)
        layout.addWidget(top_card)
        
        # 表格
        table_card = ModernCard()
        table_card.layout.setContentsMargins(SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT, SPACING_LG_INT)
        
        self.table = ModernTable()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "规格", "单位", "价格", "库存"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        table_card.add_widget(self.table)
        
        self.pagination = PaginationControl()
        self.pagination.page_changed.connect(lambda: self.load_data())
        self.pagination.size_changed.connect(lambda: self.load_data())
        table_card.add_widget(self.pagination)
        
        layout.addWidget(table_card)
        
        self.setLayout(layout)

    def on_search(self):
        self.pagination.current_page = 1
        self.load_data()

    def load_data(self):
        page = self.pagination.current_page
        size = self.pagination.page_size
        keyword = self.search_input.text()
        res = api_client.get("/drugs", params={"keyword": keyword, "page": page, "size": size})
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
            
            stock = d.get('stockQuantity', 0)
            stock_item = QTableWidgetItem(str(stock))
            if stock < 10:
                stock_item.setForeground(QColor(ERROR_COLOR))
            self.table.setItem(r, 5, stock_item)
            
            self.table.setRowHeight(r, 50)
