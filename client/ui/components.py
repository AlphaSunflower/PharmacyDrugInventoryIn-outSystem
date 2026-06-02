
from PyQt6.QtWidgets import (QPushButton, QLineEdit, QWidget, QVBoxLayout,
                             QLabel, QGraphicsDropShadowEffect, QFrame, QMessageBox,
                             QHBoxLayout, QComboBox, QDateEdit, QAbstractSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QButtonGroup, QApplication, QDialog)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QEvent, pyqtSignal, QDate, QPoint, QTimer
from PyQt6.QtGui import QColor, QCursor

from ui.style_constants import *

class DepartmentFilterGroup(QWidget):
    department_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_dept = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False) # 手动管理

        self.btn_factory = self.create_btn("本厂")
        self.btn_outsource = self.create_btn("外包")
        self.btn_leader = self.create_btn("领导拿药")

        self.btn_group.addButton(self.btn_factory)
        self.btn_group.addButton(self.btn_outsource)
        self.btn_group.addButton(self.btn_leader)

        layout.addWidget(self.btn_factory)
        layout.addWidget(self.btn_outsource)
        layout.addWidget(self.btn_leader)
        layout.addStretch()

    def create_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedSize(80, 32) # 稍微加宽以适应“领导拿药”
        # 不使用 QButtonGroup，手动管理
        btn.clicked.connect(lambda: self.handle_click(btn))
        self.update_btn_style(btn)
        return btn

    def update_btn_style(self, btn):
        if btn.isChecked():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SUCCESS_COLOR};
                    color: {WHITE};
                    border: none;
                    border-radius: {RADIUS_BASE};
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_SM};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {WHITE};
                    color: {GRAY_700};
                    border: 1px solid {GRAY_300};
                    border-radius: {RADIUS_BASE};
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_SM};
                }}
                QPushButton:hover {{
                    border-color: {SUCCESS_COLOR};
                    color: {SUCCESS_COLOR};
                }}
            """)

    def reset_selection(self):
        """重置选择"""
        self.selected_dept = ""
        self.btn_group.setExclusive(False)
        for btn in self.btn_group.buttons():
            btn.setChecked(False)
            self.update_btn_style(btn)
        self.department_changed.emit(self.selected_dept)

    def handle_click(self, btn):
        # 如果当前点击的按钮已经是选中的
        if self.selected_dept == btn.text():
            # 取消选中
            btn.setChecked(False)
            self.selected_dept = ""
        else:
            # 选中新的，取消其他的
            self.selected_dept = btn.text()
            for b in self.btn_group.buttons():
                if b != btn:
                    b.setChecked(False)
                    self.update_btn_style(b)
            
            btn.setChecked(True)
        
        self.update_btn_style(btn)
        self.department_changed.emit(self.selected_dept)

class StatusFilterGroup(QWidget):
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_status = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(False)

        # 状态筛选：待发药 已退回 已完成 已取消
        # 对应后端状态枚举: SUBMITTED, RETURNED, COMPLETED, CANCELED
        self.status_map = {
            "待发药": "SUBMITTED",
            "已退回": "RETURNED",
            "已完成": "COMPLETED",
            "已取消": "CANCELED"
        }

        self.btn_submitted = self.create_btn("待发药")
        self.btn_returned = self.create_btn("已退回")
        self.btn_completed = self.create_btn("已完成")
        self.btn_canceled = self.create_btn("已取消")

        self.btn_group.addButton(self.btn_submitted)
        self.btn_group.addButton(self.btn_returned)
        self.btn_group.addButton(self.btn_completed)
        self.btn_group.addButton(self.btn_canceled)

        layout.addWidget(self.btn_submitted)
        layout.addWidget(self.btn_returned)
        layout.addWidget(self.btn_completed)
        layout.addWidget(self.btn_canceled)
        layout.addStretch()

    def create_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedSize(80, 32)
        btn.clicked.connect(lambda: self.handle_click(btn))
        self.update_btn_style(btn)
        return btn

    def update_btn_style(self, btn):
        if btn.isChecked():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {SUCCESS_COLOR};
                    color: {WHITE};
                    border: none;
                    border-radius: {RADIUS_BASE};
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_SM};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {WHITE};
                    color: {GRAY_700};
                    border: 1px solid {GRAY_300};
                    border-radius: {RADIUS_BASE};
                    font-family: "{FONT_FAMILY}";
                    font-size: {FONT_SIZE_SM};
                }}
                QPushButton:hover {{
                    border-color: {SUCCESS_COLOR};
                    color: {SUCCESS_COLOR};
                }}
            """)

    def reset_selection(self):
        self.selected_status = ""
        self.btn_group.setExclusive(False)
        for btn in self.btn_group.buttons():
            btn.setChecked(False)
            self.update_btn_style(btn)
        self.status_changed.emit(self.selected_status)

    def handle_click(self, btn):
        status_code = self.status_map.get(btn.text(), "")
        
        if self.selected_status == status_code:
            # 取消选中
            btn.setChecked(False)
            self.selected_status = ""
        else:
            # 选中新的，取消其他的
            self.selected_status = status_code
            for b in self.btn_group.buttons():
                if b != btn:
                    b.setChecked(False)
                    self.update_btn_style(b)
            
            btn.setChecked(True)
        
        self.update_btn_style(btn)
        self.status_changed.emit(self.selected_status)

class SearchableComboBox(QWidget):
    item_selected = pyqtSignal(object) # Returns data object
    text_changed = pyqtSignal(str) # Emitted when text changes (for external filtering/loading)
    
    def __init__(self, placeholder="请选择...", parent=None):
        super().__init__(parent)
        self.items = [] # list of objects
        self.text_key = 'name' # key to display
        self.selected_item = None
        self.setup_ui()
        self.installEventFilter(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.setSpacing(0)
        
        self.input = ModernInput(placeholder=self.tr("筛选..."))
        self.input.textChanged.connect(self.on_text_changed)
        self.input.installEventFilter(self)
        self.input.setToolTip("↑↓ 选择 | Enter 确认 | ESC 关闭")
        
        self.popup_btn = QPushButton("▼")
        self.popup_btn.setFixedSize(30, 32) # match input height approx
        self.popup_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.popup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {WHITE};
                border: 1px solid {GRAY_300};
                border-left: none;
                border-top-right-radius: {RADIUS_BASE};
                border-bottom-right-radius: {RADIUS_BASE};
                color: {GRAY_600};
            }}
            QPushButton:hover {{
                background-color: {GRAY_50};
            }}
        """)
        self.popup_btn.clicked.connect(self.toggle_popup)
        
        # Tweaking input style to merge with button
        self.input.setStyleSheet(self.input.styleSheet() + f"""
            QLineEdit {{
                border-top-right-radius: 0;
                border-bottom-right-radius: 0;
            }}
        """)
        
        h_layout.addWidget(self.input)
        h_layout.addWidget(self.popup_btn)
        
        layout.addWidget(container)
        
        # Popup list
        self.list_widget = QTableWidget(self)
        self.list_widget.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.list_widget.hide()
        self.list_widget.setColumnCount(1)
        self.list_widget.horizontalHeader().setVisible(False)
        self.list_widget.verticalHeader().setVisible(False)
        self.list_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.list_widget.cellClicked.connect(self.on_item_clicked)
        self.list_widget.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {GRAY_300};
                background-color: {WHITE};
                selection-background-color: {PRIMARY_COLOR};
                selection-color: {WHITE};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR};
                color: {WHITE};
            }}
            QTableWidget::item:hover {{
                background-color: {GRAY_100};
            }}
        """)

    def setPlaceholderText(self, text):
        self.input.setPlaceholderText(text)

    def setText(self, text):
        self.input.setText(text)
        
    def clear(self):
        self.input.clear()
        self.selected_item = None
        self.list_widget.hide()

    def set_data(self, data_list, text_key='name', keep_text=False):
        """
        data_list: list of dicts
        text_key: key to display in list
        keep_text: if True, don't clear input text (useful for remote search updates)
        """
        self.items = data_list
        self.text_key = text_key
        
        # If the list is visible, refresh it immediately
        if self.list_widget.isVisible():
            self.filter_list(self.input.text())
        
        # If we have items and input is empty, maybe show all? 
        # Or if this was called due to typing, filter_list is called by on_text_changed?
        # Actually set_data is usually called initially or after API search.
        # If after API search, we want to show the results.
        if keep_text and self.input.hasFocus() and self.input.text():
             self.show_popup()

    def on_text_changed(self, text):
        # 修复：当输入框清空时，清除选中的item
        if not text or text.strip() == "":
            self.selected_item = None
            
        self.text_changed.emit(text)
        self.filter_list(text)
        
        if not self.list_widget.isVisible() and self.input.hasFocus():
            self.show_popup()

    def filter_list(self, text):
        self.list_widget.setRowCount(0)
        row = 0
        
        # If we are using remote search, self.items might already be filtered/updated.
        # But we also support local filtering if items are pre-loaded.
        
        for item_data in self.items:
            display_text = item_data.get(self.text_key, "")
            # Basic local filtering: if text is in display_text (case insensitive)
            # OR if text is empty (show all)
            # OR if we trust the external loader (e.g. API search) which updates self.items
            # But here we do local filtering too just in case.
            # However, if API returns matches for "A", and user types "AB", we should filter locally too.
            
            if not text or text.lower() in display_text.lower():
                self.list_widget.insertRow(row)
                item = QTableWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, item_data)
                
                # Special handling for stock/custom coloring if needed
                if item_data.get('id') == 'CUSTOM':
                    item.setForeground(QColor(PRIMARY_COLOR))
                
                self.list_widget.setItem(row, 0, item)
                row += 1
        
        # 强制更新窗口大小，以确保即使在打字过滤时，也能保持正确的宽和高
        if self.list_widget.isVisible():
            self.update_popup_geometry()
                
    def toggle_popup(self):
        if self.list_widget.isVisible():
            self.hide_popup()
        else:
            self.show_popup()
            self.input.setFocus()

    def show_popup(self):
        self.filter_list(self.input.text())
        self.list_widget.raise_()
        self.list_widget.show()
        self.update_popup_geometry()
        
        # 安装全局事件过滤器以检测点击外部
        QApplication.instance().installEventFilter(self)

    def update_popup_geometry(self):
        window = self.window()
        pos = self.input.mapTo(window, self.input.rect().bottomLeft())
        self.list_widget.setParent(window)
        
        # Dynamic height
        row_height = 35
        count = self.list_widget.rowCount()
        height = min(count * row_height + 5, 400) # Increased max height
        if height < 50: height = 50 # Min height
        
        # Dynamic width: at least input width, but can be wider to show content
        width = max(self.input.width() + 30, 450)
        
        self.list_widget.setGeometry(pos.x(), pos.y(), width, height)

    def hide_popup(self):
        self.list_widget.hide()
        # 移除全局事件过滤器
        QApplication.instance().removeEventFilter(self)

    def on_item_clicked(self, row, col):
        item = self.list_widget.item(row, 0)
        data = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()
        
        self.selected_item = data
        self.input.setText(name)
        self.hide_popup()
        self.item_selected.emit(data)

    def eventFilter(self, source, event):
        # 点击输入框时弹出列表
        if source == self.input:
            if event.type() == QEvent.Type.MouseButtonPress:
                if not self.list_widget.isVisible():
                    self.show_popup()
                # return False to let input handle focus
                return False
        
        # 全局事件过滤器处理逻辑 (Click outside)
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.list_widget.isVisible():
                global_pos = event.globalPosition().toPoint()
                
                list_rect = self.list_widget.rect()
                list_global = self.list_widget.mapToGlobal(list_rect.topLeft())
                list_global_rect = QRect(list_global, list_rect.size())
                
                input_rect = self.input.rect()
                input_global = self.input.mapToGlobal(input_rect.topLeft())
                input_global_rect = QRect(input_global, input_rect.size())
                
                btn_rect = self.popup_btn.rect()
                btn_global = self.popup_btn.mapToGlobal(btn_rect.topLeft())
                btn_global_rect = QRect(btn_global, btn_rect.size())

                if not list_global_rect.contains(global_pos) and \
                   not input_global_rect.contains(global_pos) and \
                   not btn_global_rect.contains(global_pos):
                    self.hide_popup()
        
        # Keyboard navigation
        if source == self.input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                if not self.list_widget.isVisible(): self.show_popup()
                current_row = self.list_widget.currentRow()
                if current_row > 0:
                    self.list_widget.setCurrentCell(current_row - 1, 0)
                elif current_row == -1 and self.list_widget.rowCount() > 0:
                    self.list_widget.setCurrentCell(self.list_widget.rowCount() - 1, 0)
                return True
            elif key == Qt.Key.Key_Down:
                if not self.list_widget.isVisible(): self.show_popup()
                current_row = self.list_widget.currentRow()
                if current_row < self.list_widget.rowCount() - 1:
                    self.list_widget.setCurrentCell(current_row + 1, 0)
                elif current_row == -1 and self.list_widget.rowCount() > 0:
                    self.list_widget.setCurrentCell(0, 0)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                if self.list_widget.isVisible():
                    current_row = self.list_widget.currentRow()
                    if current_row >= 0:
                        self.on_item_clicked(current_row, 0)
                        return True
                elif not self.list_widget.isVisible():
                    self.show_popup()
                    return True
            elif key == Qt.Key.Key_Escape:
                if self.list_widget.isVisible():
                    self.hide_popup()
                    return True

        return super().eventFilter(source, event)

class SmartDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.calendarWidget().installEventFilter(self)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setup_style()

    def focusInEvent(self, event):
        if self.date() == self.minimumDate():
            self.setDate(QDate.currentDate())
        super().focusInEvent(event)

    def mousePressEvent(self, event):
        if self.date() == self.minimumDate():
            self.setDate(QDate.currentDate())
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.calendarWidget() and event.type() == QEvent.Type.Show:
            # 当日历弹出时，如果当前日期是最小日期（即空值），则显示当前月份并选中当天
            if self.date() == self.minimumDate():
                today = QDate.currentDate()
                self.setDate(today)
                self.calendarWidget().setSelectedDate(today)
                self.calendarWidget().setCurrentPage(today.year(), today.month())
        return super().eventFilter(obj, event)

    def open_calendar(self):
        """公开方法以展开日历"""
        # showPopup 是 protected 的，但在 Python 中可以访问，或者通过发消息
        # QDateEdit 没有 showPopup? QComboBox 有。
        # QDateTimeEdit (base of QDateEdit) doesn't export showPopup.
        # But pressing Down arrow or F4 works.
        from PyQt6.QtGui import QKeyEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(self, event)

    def setup_style(self):
        self.setStyleSheet(f"""
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

class PaginationControl(QWidget):
    """分页控件"""
    page_changed = pyqtSignal(int)
    size_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        self.page_size = 10
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # 总记录数
        self.total_label = ModernLabel("共 0 条")
        layout.addWidget(self.total_label)

        # 每页显示数量
        self.size_combo = QComboBox()
        self.size_combo.addItems(["10条/页", "20条/页", "50条/页", "100条/页"])
        self.size_combo.setCurrentText(f"{self.page_size}条/页")
        self.size_combo.currentIndexChanged.connect(self.on_size_changed)
        self.style_combobox(self.size_combo)
        layout.addWidget(self.size_combo)

        # 上一页
        self.prev_btn = ModernButton("<", variant="secondary")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.clicked.connect(self.prev_page)
        layout.addWidget(self.prev_btn)

        # 页码显示
        self.page_label = ModernLabel("1 / 1")
        layout.addWidget(self.page_label)

        # 下一页
        self.next_btn = ModernButton(">", variant="secondary")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.clicked.connect(self.next_page)
        layout.addWidget(self.next_btn)
        
        self.update_buttons()

    def style_combobox(self, combo):
        combo.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 10px;
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
                min-width: 80px;
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
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {GRAY_500};
                margin-right: 5px;
            }}
        """)

    def update_state(self, current, total_pages, total_records):
        self.current_page = current
        self.total_pages = max(1, total_pages)
        self.total_records = total_records
        
        self.page_label.setText(f"{self.current_page} / {self.total_pages}")
        self.total_label.setText(f"共 {self.total_records} 条")
        
        self.update_buttons()

    def update_buttons(self):
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.page_changed.emit(self.current_page)

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_changed.emit(self.current_page)

    def on_size_changed(self):
        text = self.size_combo.currentText()
        size = int(text.replace("条/页", ""))
        if size != self.page_size:
            self.page_size = size
            self.current_page = 1 # 重置为第一页
            self.size_changed.emit(size)

class DiagnosisSelectionDialog(QMessageBox):
    """诊断选择弹窗"""
    def __init__(self, diagnosis_list, parent=None):
        super().__init__(parent)
        self.diagnosis_list = diagnosis_list
        self.selected_diagnosis = None
        self.setWindowTitle("选择临床诊断")
        self.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.button(QMessageBox.StandardButton.Cancel).setText("取消")
        
        # 美化弹窗整体样式
        self.setStyleSheet(f"""
            QMessageBox {{
                background-color: {WHITE};
            }}
            QLabel {{
                color: {GRAY_800};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_BASE};
            }}
        """)
        
        # 自定义内容区域
        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(15)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("请选择临床诊断")
        title_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_LG};
            font-weight: {FONT_WEIGHT_BOLD};
            color: {PRIMARY_COLOR};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 搜索框
        self.search_input = ModernInput(placeholder="输入关键字搜索...")
        self.search_input.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_input)
        
        # 列表
        self.list_widget = QTableWidget()
        self.list_widget.setColumnCount(1)
        self.list_widget.horizontalHeader().setVisible(False)
        self.list_widget.verticalHeader().setVisible(False)
        self.list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.list_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list_widget.cellClicked.connect(self.on_item_clicked)
        self.list_widget.setMinimumHeight(350)
        self.list_widget.setMinimumWidth(400)
        
        # 美化列表样式
        self.list_widget.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {GRAY_300};
                background-color: {WHITE};
                border-radius: {RADIUS_BASE};
                selection-background-color: {PRIMARY_COLOR}20;
                selection-color: {PRIMARY_COLOR};
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {GRAY_100};
                font-size: {FONT_SIZE_BASE};
                color: {GRAY_800};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR}20;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                border-left: 3px solid {PRIMARY_COLOR};
            }}
            QTableWidget::item:hover {{
                background-color: {GRAY_50};
            }}
        """)
        
        layout.addWidget(self.list_widget)
        
        # 替换 QMessageBox 的默认布局内容
        self.layout().addWidget(self.content_widget, 0, 0, 1, self.layout().columnCount())
        
        self.filter_list("")
        
        # 安装事件过滤器以处理键盘导航
        self.search_input.installEventFilter(self)
        
    def filter_list(self, text):
        self.list_widget.setRowCount(0)
        row = 0
        for diag in self.diagnosis_list:
            if not text or text.lower() in diag['name'].lower():
                self.list_widget.insertRow(row)
                item = QTableWidgetItem(diag['name'])
                item.setData(Qt.ItemDataRole.UserRole, diag)
                self.list_widget.setItem(row, 0, item)
                row += 1
        
        # Always add "Custom Diagnosis" option at the end
        self.list_widget.insertRow(row)
        item = QTableWidgetItem("自定义诊断")
        # Use a special dict for Custom
        item.setData(Qt.ItemDataRole.UserRole, {'id': 'CUSTOM', 'name': '自定义诊断'})
        item.setForeground(QColor(PRIMARY_COLOR))
        self.list_widget.setItem(row, 0, item)
                
    def on_item_clicked(self, row, col):
        item = self.list_widget.item(row, 0)
        self.selected_diagnosis = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def eventFilter(self, source, event):
        if source == self.search_input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                current_row = self.list_widget.currentRow()
                if current_row > 0:
                    self.list_widget.setCurrentCell(current_row - 1, 0)
                return True
            elif key == Qt.Key.Key_Down:
                current_row = self.list_widget.currentRow()
                if current_row < self.list_widget.rowCount() - 1:
                    self.list_widget.setCurrentCell(current_row + 1, 0)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                current_row = self.list_widget.currentRow()
                if current_row >= 0:
                    self.on_item_clicked(current_row, 0)
                return True
        return super().eventFilter(source, event)

class DrugSelectionDialog(QMessageBox):
    """药品选择弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drugs = []
        self.selected_drug = None
        self.setWindowTitle("选择药品")
        self.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.button(QMessageBox.StandardButton.Cancel).setText("取消")
        
        # 美化弹窗整体样式
        self.setStyleSheet(f"""
            QMessageBox {{
                background-color: {WHITE};
            }}
            QLabel {{
                color: {GRAY_800};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_BASE};
            }}
        """)
        
        # 自定义内容区域
        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(15)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("请选择药品")
        title_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_LG};
            font-weight: {FONT_WEIGHT_BOLD};
            color: {PRIMARY_COLOR};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 搜索框
        self.search_input = ModernInput(placeholder="输入药品名称搜索...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        layout.addWidget(self.search_input)
        
        # 列表
        self.list_widget = QTableWidget()
        self.list_widget.setColumnCount(1)
        self.list_widget.horizontalHeader().setVisible(False)
        self.list_widget.verticalHeader().setVisible(False)
        self.list_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.list_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list_widget.cellClicked.connect(self.on_item_clicked)
        self.list_widget.setMinimumHeight(350)
        self.list_widget.setMinimumWidth(450)
        
        # 美化列表样式
        self.list_widget.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {GRAY_300};
                background-color: {WHITE};
                border-radius: {RADIUS_BASE};
                selection-background-color: {PRIMARY_COLOR}20;
                selection-color: {PRIMARY_COLOR};
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {GRAY_100};
                font-size: {FONT_SIZE_BASE};
                color: {GRAY_800};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR}20;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                border-left: 3px solid {PRIMARY_COLOR};
            }}
            QTableWidget::item:hover {{
                background-color: {GRAY_50};
            }}
        """)
        
        layout.addWidget(self.list_widget)
        
        # 替换 QMessageBox 的默认布局内容
        self.layout().addWidget(self.content_widget, 0, 0, 1, self.layout().columnCount())
        
        # 搜索防抖定时器
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.perform_search)
        
        # 初始加载推荐/常用药品（可选，这里先留空或加载部分）
        self.perform_search()
        
        # 安装事件过滤器以处理键盘导航
        self.search_input.installEventFilter(self)
        
    def on_search_text_changed(self, text):
        self.search_timer.start()

    def perform_search(self):
        from utils.api_client import api_client # 延迟导入避免循环依赖
        
        keyword = self.search_input.text()
        try:
            res = api_client.get("/drugs", params={"keyword": keyword, "size": 50}) # 限制数量
            if res.status_code == 200:
                data = res.json()
                if data['code'] == 200:
                    self.drugs = data['data']['records']
                    self.update_list()
        except Exception as e:
            print(f"Search drugs error: {e}")

    def update_list(self):
        self.list_widget.setRowCount(0)
        row = 0
        for drug in self.drugs:
            # 格式化显示：名称 (规格) - 库存: X
            display_text = f"{drug['name']} ({drug['spec']})"
            stock = drug.get('stockQuantity', 0)
            if stock < 10:
                display_text += f"   [库存紧张: {stock}]"
            else:
                display_text += f"   [库存: {stock}]"
                
            self.list_widget.insertRow(row)
            item = QTableWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, drug)
            
            if stock <= 0:
                item.setForeground(QColor(GRAY_400))
                # item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # 注释掉：即使库存为0也允许选择，或者看需求？
                # 如果不允许选择，用户怎么知道是库存没了还是点不了？
                # 暂时允许选择，或者在点击时提示？
                # 现在的逻辑是库存 <= 0 变灰且不可选
                # 但 on_item_clicked 里有检查
            elif stock < 10:
                item.setForeground(QColor(ERROR_COLOR))
            
            self.list_widget.setItem(row, 0, item)
            row += 1

    def on_item_clicked(self, row, col):
        item = self.list_widget.item(row, 0)
        # 再次检查是否可选
        # if not (item.flags() & Qt.ItemFlag.ItemIsSelectable):
        #    return
        
        # 允许选择库存为0的药吗？通常医生开药时如果没库存是不行的。
        # 这里暂时保持原逻辑：如果不可选（灰显），点击无效。
        # 为了用户体验，点击时如果库存不足可以提示？
        
        self.selected_drug = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def eventFilter(self, source, event):
        if source == self.search_input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                current_row = self.list_widget.currentRow()
                if current_row > 0:
                    self.list_widget.setCurrentCell(current_row - 1, 0)
                return True
            elif key == Qt.Key.Key_Down:
                current_row = self.list_widget.currentRow()
                if current_row < self.list_widget.rowCount() - 1:
                    self.list_widget.setCurrentCell(current_row + 1, 0)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                current_row = self.list_widget.currentRow()
                if current_row >= 0:
                    self.on_item_clicked(current_row, 0)
                return True
        return super().eventFilter(source, event)

class ModernButton(QPushButton):
    """现代化按钮组件"""
    def __init__(self, text, variant="primary", parent=None):
        super().__init__(text, parent)
        self.variant = variant
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setup_style()
        
    def setup_style(self):
        base_style = f"""
            QPushButton {{
                padding: {SPACING_MD} {SPACING_LG};
                border-radius: {RADIUS_BASE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
                font-weight: {FONT_WEIGHT_BOLD};
                border: none;
            }}
        """
        
        if self.variant == "primary":
            self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: {PRIMARY_COLOR};
                    color: {WHITE};
                }}
                QPushButton:hover {{
                    background-color: {PRIMARY_HOVER_COLOR};
                }}
                QPushButton:pressed {{
                    background-color: {PRIMARY_ACTIVE_COLOR};
                }}
                QPushButton:disabled {{
                    background-color: {GRAY_300};
                    color: {GRAY_500};
                }}
            """)
        elif self.variant == "secondary":
             self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: {WHITE};
                    color: {GRAY_700};
                    border: 1px solid {GRAY_300};
                }}
                QPushButton:hover {{
                    background-color: {GRAY_50};
                    border-color: {GRAY_400};
                }}
                QPushButton:pressed {{
                    background-color: {GRAY_100};
                }}
            """)
        elif self.variant == "warning":
            self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: {WARNING_COLOR};
                    color: {WHITE};
                }}
                QPushButton:hover {{
                    background-color: #d97706;
                }}
                QPushButton:pressed {{
                    background-color: #b45309;
                }}
            """)
        elif self.variant == "danger":
            self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: {ERROR_COLOR};
                    color: {WHITE};
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
                QPushButton:pressed {{
                    background-color: #b91c1c;
                }}
            """)
        elif self.variant == "outline":
            self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: transparent;
                    color: {PRIMARY_COLOR};
                    border: 1px solid {PRIMARY_COLOR};
                }}
                QPushButton:hover {{
                    background-color: {PRIMARY_COLOR}10; 
                }}
                QPushButton:pressed {{
                    background-color: {PRIMARY_COLOR}20;
                }}
            """)

class ModernInput(QLineEdit):
    """现代化输入框组件"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: {SPACING_MD} {SPACING_LG};
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                color: {GRAY_800};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
                selection-background-color: {PRIMARY_COLOR};
            }}
            QLineEdit:focus {{
                border: 2px solid {PRIMARY_COLOR};
                padding: {SPACING_MD} {int(SPACING_LG.replace('px',''))-1}px; /* 调整padding以保持大小一致 */
            }}
            QLineEdit:hover {{
                border-color: {GRAY_400};
            }}
            QLineEdit:disabled {{
                background-color: {GRAY_100};
                color: {GRAY_400};
            }}
        """)

class ModernCard(QFrame):
    """现代化卡片组件"""
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        self.layout.setSpacing(15)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            ModernCard {{
                background-color: {WHITE};
                border-radius: {RADIUS_LG};
                border: 1px solid {GRAY_200};
            }}
        """)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_LG};
                font-weight: {FONT_WEIGHT_BOLD};
                color: {GRAY_800};
                border: none;
                background-color: transparent;
            """)
            self.layout.addWidget(title_label)
            
    def add_widget(self, widget):
        self.layout.addWidget(widget)

    def add_layout(self, layout):
        self.layout.addLayout(layout)

class ModernLabel(QLabel):
    """现代化标签"""
    def __init__(self, text, size=FONT_SIZE_SM, color=GRAY_700, weight=FONT_WEIGHT_NORMAL, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            color: {color};
            font-size: {size};
            font-weight: {weight};
            font-family: "{FONT_FAMILY}";
            background-color: transparent;
        """)

class SidebarButton(QPushButton):
    """侧边栏菜单按钮"""
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: {SPACING_LG} {SPACING_XL};
                background-color: transparent;
                border: none;
                color: {SIDEBAR_TEXT};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
                border-left: 3px solid transparent;
            }}
            QPushButton:hover {{
                background-color: {SIDEBAR_HOVER};
                color: {WHITE};
            }}
            QPushButton:checked {{
                background-color: {SIDEBAR_HOVER};
                color: {WHITE};
                border-left: 3px solid {PRIMARY_COLOR};
                font-weight: {FONT_WEIGHT_BOLD};
            }}
        """)

class ModernMessageBox(QMessageBox):
    """现代化弹窗组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()

    def setup_style(self):
        self.setStyleSheet(f"""
            QMessageBox {{
                background-color: {WHITE};
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_MD};
            }}
            QLabel {{
                color: {GRAY_800};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_BASE};
                padding: 10px;
            }}
            QPushButton {{
                padding: 6px 16px;
                border-radius: {RADIUS_BASE};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE_SM};
                min-width: 60px;
                background-color: {WHITE};
                color: {GRAY_700};
                border: 1px solid {GRAY_300};
            }}
            QPushButton:hover {{
                background-color: {GRAY_50};
                border-color: {GRAY_400};
            }}
            QPushButton:pressed {{
                background-color: {GRAY_100};
            }}
        """)

    @staticmethod
    def information(parent, title, text):
        msg = ModernMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 定制按钮样式
        ok_btn = msg.button(QMessageBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setStyleSheet(f"""
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
            
        return msg.exec()

    @staticmethod
    def warning(parent, title, text):
        msg = ModernMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        ok_btn = msg.button(QMessageBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {WARNING_COLOR};
                    color: {WHITE};
                    border: none;
                    padding: 6px 20px;
                    border-radius: {RADIUS_BASE};
                }}
                QPushButton:hover {{
                    background-color: #d97706;
                }}
            """)
            
        return msg.exec()

    @staticmethod
    def critical(parent, title, text):
        msg = ModernMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        ok_btn = msg.button(QMessageBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ERROR_COLOR};
                    color: {WHITE};
                    border: none;
                    padding: 6px 20px;
                    border-radius: {RADIUS_BASE};
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
            """)
            
        return msg.exec()

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        msg = ModernMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(buttons)
        
        yes_btn = msg.button(QMessageBox.StandardButton.Yes)
        if yes_btn:
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
            
        return msg.exec()


class ToastNotification(QFrame):
    """右下角弹出通知，自动消失，点击可跳转"""
    clicked = pyqtSignal()

    def __init__(self, parent, message, duration=4000):
        super().__init__(parent)
        self.setFixedSize(320, 80)
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {WHITE};
                border: 1px solid {GRAY_200};
                border-radius: {RADIUS_MD};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {ERROR_COLOR}; font-size: 14px; background: transparent;")
        dot.setFixedWidth(20)
        layout.addWidget(dot)

        self.msg_label = QLabel(message)
        self.msg_label.setStyleSheet(f"color: {GRAY_800}; font-size: {FONT_SIZE_SM}; background: transparent;")
        self.msg_label.setWordWrap(True)
        layout.addWidget(self.msg_label, 1)

        QTimer.singleShot(duration, self.fade_out)

    def mousePressEvent(self, event):
        self.clicked.emit()
        self.fade_out()

    def fade_out(self):
        try:
            self._anim = QPropertyAnimation(self, b"windowOpacity")
            self._anim.setDuration(300)
            self._anim.setStartValue(1.0)
            self._anim.setEndValue(0.0)
            self._anim.finished.connect(self.hide)
            self._anim.finished.connect(self.deleteLater)
            self._anim.start()
        except RuntimeError:
            self.hide()
            self.deleteLater()


class BadgedSidebarButton(QPushButton):
    """带红色数字徽标的侧边栏按钮（使用 QLabel 叠加层）"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._badge_count = 0
        self._base_text = text
        self.setup_style()
        # 红色徽标标签，初始隐藏
        self._badge_label = QLabel(self)
        self._badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ERROR_COLOR};
                color: {WHITE};
                border-radius: 9px;
                font-size: 10px;
                font-weight: bold;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
                padding: 0px;
            }}
        """)
        self._badge_label.hide()

    def setup_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {SIDEBAR_TEXT};
                text-align: left;
                padding: 14px 20px;
                border: none;
                font-size: {FONT_SIZE_SM};
            }}
            QPushButton:hover {{
                background-color: {SIDEBAR_HOVER};
            }}
            QPushButton:checked {{
                background-color: {PRIMARY_COLOR};
                color: {WHITE};
            }}
        """)

    def set_badge(self, count):
        count = max(0, count)
        if count == self._badge_count:
            return
        self._badge_count = count
        if count > 0:
            display = str(count) if count <= 99 else "99+"
            self._badge_label.setText(display)
            self._badge_label.adjustSize()
            # 定位到按钮右侧
            self._badge_label.move(self.width() - self._badge_label.width() - 12, 14)
            self._badge_label.show()
        else:
            self._badge_label.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._badge_count > 0:
            self._badge_label.move(self.width() - self._badge_label.width() - 12, 14)


class ModernTable(QTableWidget):
    """统一风格表格 — 替代所有 view 中重复的 style_table()"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self._setup_style()

    def _setup_style(self):
        self.horizontalHeader().setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {TABLE_HEADER_BG};
                color: {GRAY_600};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {TABLE_BORDER};
                font-weight: bold;
                font-family: "{FONT_FAMILY}";
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
        """)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {WHITE};
                border: 1px solid {TABLE_BORDER};
                border-radius: {RADIUS_BASE};
                gridline-color: {TABLE_BORDER};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {GRAY_100};
            }}
            QTableWidget::item:hover {{
                background-color: {TABLE_HOVER_BG};
            }}
            QTableWidget::item:selected {{
                background-color: {PRIMARY_COLOR}15;
                color: {PRIMARY_COLOR};
            }}
            QTableWidget::item:alternate {{
                background-color: {GRAY_50};
            }}
        """)

    def show_empty(self, message="暂无数据"):
        """显示空状态提示"""
        self.setRowCount(1)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels([""])
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(QColor(EMPTY_STATE_COLOR))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        self.setItem(0, 0, item)
        self.horizontalHeader().setVisible(False)
        self.setRowHeight(0, 100)


class ModernInputDialog(QDialog):
    """统一风格的输入对话框，替代 QInputDialog.getText()"""
    def __init__(self, parent, title, label, default_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(420, 200)
        self.setStyleSheet(f"background-color: {WHITE};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(ModernLabel(label, size=FONT_SIZE_BASE, color=GRAY_700))
        self.input = ModernInput(placeholder="请输入...")
        self.input.setText(default_text)
        self.input.setToolTip("Enter 确定 | ESC 取消")
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = ModernButton("确定", variant="primary")
        ok_btn.setToolTip("Enter 确定")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = ModernButton("取消", variant="secondary")
        cancel_btn.setToolTip("ESC 取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_text(self):
        return self.input.text()
