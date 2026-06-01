# 药品出入库系统 UI 设计规范

## 1. 设计原则

### 1.1 视觉层次
- 使用清晰的信息层级，重要信息优先展示
- 采用卡片式布局，增强内容模块化
- 合理的留白和间距，避免界面拥挤

### 1.2 色彩系统
- 主色调：#2563eb (蓝色) - 专业、可信
- 辅助色：#10b981 (绿色) - 成功、通过
- 警告色：#f59e0b (橙色) - 提醒、注意
- 错误色：#ef4444 (红色) - 错误、危险
- 中性色：#6b7280 (灰色) - 次要信息

### 1.3 字体系统
- 标题：16px，加粗，#1f2937
- 正文：14px，常规，#374151
- 次要文字：12px，#6b7280
- 代码/数字：等宽字体

### 1.4 间距规范
- 组件间距：16px
- 内容内边距：12px
- 卡片圆角：8px
- 按钮圆角：6px

## 2. 组件规范

### 2.1 按钮规范
```python
# 主要按钮
QPushButton {
    background-color: #2563eb;
    color: white;
    padding: 10px 16px;
    border-radius: 6px;
    border: none;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}

# 次要按钮
QPushButton.secondary {
    background-color: #f3f4f6;
    color: #374151;
    border: 1px solid #d1d5db;
}
```

### 2.2 输入框规范
```python
QLineEdit {
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background-color: white;
    color: #374151;
}
QLineEdit:focus {
    border-color: #2563eb;
    outline: none;
}
QLineEdit:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
}
```

### 2.3 表格规范
```python
QTableWidget {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: white;
}
QHeaderView::section {
    background-color: #f9fafb;
    padding: 8px;
    border: none;
    font-weight: 600;
    color: #374151;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f3f4f6;
}
QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}
```

## 3. 布局规范

### 3.1 主界面布局
- 左侧导航栏：200px 固定宽度
- 右侧内容区：自适应宽度
- 顶部标题栏：60px 高度
- 内容区域边距：20px

### 3.2 卡片布局
```python
# 卡片容器
QWidget.card {
    background-color: white;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    padding: 16px;
}
```

### 3.3 表单布局
- 标签宽度：100px
- 输入框间距：12px
- 按钮组间距：8px

## 4. 交互规范

### 4.1 悬停效果
- 按钮：背景色变深 10%
- 链接：下划线出现
- 表格行：背景色 #f9fafb

### 4.2 点击反馈
- 按钮：缩放效果 0.98
- 链接：颜色变深
- 卡片：轻微阴影

### 4.3 加载状态
- 旋转动画：1秒完成一圈
- 骨架屏：灰色渐变
- 进度条：蓝色渐变

## 5. 可访问性

### 5.1 颜色对比
- 文字与背景对比度：≥4.5:1
- 交互元素对比度：≥3:1

### 5.2 键盘导航
- Tab键顺序合理
- 焦点指示器清晰可见
- 快捷键支持

### 5.3 屏幕阅读器
- 所有图像有alt文本
- 表单有label关联
- 状态变化有通知

## 6. 性能优化

### 6.1 动画优化
- 使用GPU加速的属性
- 动画时长：200-300ms
- 避免同时多个复杂动画

### 6.2 资源优化
- 图标使用矢量格式
- 图片适当压缩
- 样式表合并最小化

## 7. 实现步骤

1. **创建基础样式模块**
2. **重构登录界面**
3. **重构主界面布局**
4. **统一所有组件样式**
5. **添加交互动画**
6. **优化响应式布局**
7. **测试可访问性**
8. **性能调优**