# 药品出入库系统 UI 美化方案

## 项目概述
基于 PyQt6 的桌面应用程序，需要全面提升视觉设计和用户体验。

## 当前状态分析
- 技术栈：Python + PyQt6
- 现有组件：基础表单、表格、按钮、输入框
- 当前问题：样式零散、缺乏统一设计系统、交互反馈不足

## 设计目标
1. **现代化**：采用2024年流行的设计趋势
2. **专业性**：符合医疗行业专业形象
3. **易用性**：直观的操作流程和清晰的视觉层次
4. **一致性**：统一的视觉语言和交互模式

## 设计系统

### 色彩方案
```python
# 主色调 - 医疗专业蓝
PRIMARY = "#2563eb"      # 专业蓝
PRIMARY_HOVER = "#1d4ed8"
PRIMARY_ACTIVE = "#1e40af"

# 辅助色
SUCCESS = "#10b981"     # 成功绿
WARNING = "#f59e0b"     # 警告橙  
ERROR = "#ef4444"       # 错误红
INFO = "#3b82f6"        # 信息蓝

# 中性色
GRAY_50 = "#f9fafb"     # 背景灰
GRAY_100 = "#f3f4f6"
GRAY_200 = "#e5e7eb"
GRAY_300 = "#d1d5db"
GRAY_400 = "#9ca3af"
GRAY_500 = "#6b7280"
GRAY_600 = "#4b5563"
GRAY_700 = "#374151"
GRAY_800 = "#1f2937"
GRAY_900 = "#111827"

# 白色和黑色
WHITE = "#ffffff"
BLACK = "#000000"
```

### 字体系统
```python
# 字体大小
FONT_SIZE_XS = "12px"
FONT_SIZE_SM = "14px"   
FONT_SIZE_BASE = "16px"
FONT_SIZE_LG = "18px"
FONT_SIZE_XL = "20px"
FONT_SIZE_2XL = "24px"

# 字重
FONT_WEIGHT_NORMAL = "400"
FONT_WEIGHT_MEDIUM = "500"
FONT_WEIGHT_SEMIBOLD = "600"
FONT_WEIGHT_BOLD = "700"

# 行高
LINE_HEIGHT_TIGHT = "1.25"
LINE_HEIGHT_NORMAL = "1.5"
LINE_HEIGHT_RELAXED = "1.75"
```

### 间距系统
```python
# 间距单位（基于4px网格）
SPACING_1 = "4px"     # xs
SPACING_2 = "8px"     # sm
SPACING_3 = "12px"    # md
SPACING_4 = "16px"    # lg
SPACING_5 = "20px"    # xl
SPACING_6 = "24px"    # 2xl
SPACING_8 = "32px"    # 3xl
SPACING_10 = "40px"   # 4xl
SPACING_12 = "48px"   # 5xl
```

### 圆角系统
```python
# 圆角大小
RADIUS_NONE = "0px"
RADIUS_SM = "4px"
RADIUS_BASE = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
RADIUS_FULL = "9999px"
```

### 阴影系统
```python
# 阴影效果
SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
SHADOW_BASE = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
SHADOW_XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
```

## 组件设计

### 按钮组件
```python
class ModernButton(QPushButton):
    def __init__(self, text, variant="primary"):
        super().__init__(text)
        self.variant = variant
        self.setup_style()
        
    def setup_style(self):
        base_style = f"""
            QPushButton {{
                padding: {SPACING_3} {SPACING_4};
                border-radius: {RADIUS_BASE};
                font-weight: {FONT_WEIGHT_MEDIUM};
                border: none;
                transition: all 0.2s ease;
            }}
        """
        
        if self.variant == "primary":
            self.setStyleSheet(base_style + f"""
                QPushButton {{
                    background-color: {PRIMARY};
                    color: {WHITE};
                }}
                QPushButton:hover {{
                    background-color: {PRIMARY_HOVER};
                    box-shadow: {SHADOW_MD};
                }}
                QPushButton:pressed {{
                    background-color: {PRIMARY_ACTIVE};
                    transform: scale(0.98);
                }}
            """)
```

### 输入框组件
```python
class ModernInput(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setup_style()
        
    def setup_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: {SPACING_3} {SPACING_4};
                border: 1px solid {GRAY_300};
                border-radius: {RADIUS_BASE};
                background-color: {WHITE};
                color: {GRAY_700};
                font-size: {FONT_SIZE_BASE};
                transition: all 0.2s ease;
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY};
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }}
            QLineEdit:hover {{
                border-color: {GRAY_400};
            }}
            QLineEdit:disabled {{
                background-color: {GRAY_100};
                color: {GRAY_400};
            }}
        """)
```

### 卡片组件
```python
class ModernCard(QWidget):
    def __init__(self, title=""):
        super().__init__()
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACING_4, SPACING_4, SPACING_4, SPACING_4)
        
        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_LG};
                font-weight: {FONT_WEIGHT_SEMIBOLD};
                color: {GRAY_800};
                margin-bottom: {SPACING_3};
            """)
            layout.addWidget(title_label)
        
        self.setLayout(layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {WHITE};
                border-radius: {RADIUS_MD};
                border: 1px solid {GRAY_200};
                box-shadow: {SHADOW_BASE};
            }}
            QWidget:hover {{
                box-shadow: {SHADOW_MD};
                border-color: {GRAY_300};
            }}
        """)
```

## 布局系统

### 网格布局
```python
class GridLayout(QGridLayout):
    def __init__(self, spacing=SPACING_4):
        super().__init__()
        self.setSpacing(spacing)
        self.setContentsMargins(spacing, spacing, spacing, spacing)
```

### 响应式布局
```python
class ResponsiveLayout(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.setup_responsive_behavior()
        
    def setup_responsive_behavior(self):
        # 根据屏幕尺寸调整间距
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        
        if screen_size.width() > 1920:
            self.setSpacing(SPACING_6)
        elif screen_size.width() > 1366:
            self.setSpacing(SPACING_5)
        else:
            self.setSpacing(SPACING_4)
```

## 动画系统

### 过渡动画
```python
class AnimatedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        
    def show_with_animation(self):
        self.animation.setStartValue(QRect(self.x(), self.y() - 20, self.width(), self.height()))
        self.animation.setEndValue(QRect(self.x(), self.y(), self.width(), self.height()))
        self.animation.start()
        self.show()
```

### 微交互动画
```python
class HoverButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setup_hover_animation()
        
    def setup_hover_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.hover_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hover_animation.setDuration(150)
        
    def enterEvent(self, event):
        self.hover_animation.setStartValue(1.0)
        self.hover_animation.setEndValue(0.8)
        self.hover_animation.start()
        
    def leaveEvent(self, event):
        self.hover_animation.setStartValue(0.8)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
```

## 可访问性

### 键盘导航
```python
class AccessibleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_keyboard_navigation()
        
    def setup_keyboard_navigation(self):
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTabOrder(self.widget1, self.widget2)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Space:
            self.click()
        elif event.key() == Qt.Key_Escape:
            self.close()
```

### 屏幕阅读器支持
```python
class ScreenReaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_accessibility()
        
    def setup_accessibility(self):
        self.setAccessibleName("主要操作区域")
        self.setAccessibleDescription("包含所有主要功能的操作界面")
        
        for child in self.findChildren(QWidget):
            if hasattr(child, 'text'):
                child.setAccessibleName(child.text())
                child.setAccessibleDescription(f"点击{child.text()}执行相关操作")
```

## 性能优化

### 样式表优化
```python
class OptimizedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_optimized_styles()
        
    def setup_optimized_styles(self):
        # 合并样式表，减少重复
        combined_style = f"""
            QWidget {{
                background-color: {GRAY_50};
                color: {GRAY_800};
            }}
            QPushButton {{
                {self.get_button_style()}
            }}
            QLineEdit {{
                {self.get_input_style()}
            }}
        """
        self.setStyleSheet(combined_style)
```

### 资源管理
```python
class ResourceManager:
    _instance = None
    _icons = {}
    _styles = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_icon(self, name):
        if name not in self._icons:
            self._icons[name] = QIcon(f":/icons/{name}.svg")
        return self._icons[name]
```

## 实施计划

### 第一阶段：基础组件（1-2天）
1. 创建设计系统常量文件
2. 实现基础按钮、输入框组件
3. 建立样式管理器

### 第二阶段：布局系统（2-3天）
1. 重构主界面布局
2. 实现响应式网格系统
3. 创建卡片组件

### 第三阶段：高级组件（3-4天）
1. 美化表格组件
2. 实现动画系统
3. 创建高级交互组件

### 第四阶段：细节优化（2-3天）
1. 添加微交互动画
2. 优化可访问性
3. 性能调优

### 第五阶段：测试和文档（1-2天）
1. 跨平台兼容性测试
2. 创建组件库文档
3. 用户测试和反馈收集

## 预期效果

1. **视觉提升**：现代化、专业的外观
2. **体验优化**：流畅的交互和清晰的反馈
3. **开发效率**：可复用的组件系统
4. **维护便利**：统一的设计语言和规范