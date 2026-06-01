
# 药品出入库系统 UI 设计规范 - 样式常量

# ==========================================
# 1. 色彩系统
# ==========================================

# 主色调 - 医疗专业蓝
PRIMARY_COLOR = "#2563eb"      # 专业蓝
PRIMARY_HOVER_COLOR = "#1d4ed8"
PRIMARY_ACTIVE_COLOR = "#1e40af"

# 辅助色
SUCCESS_COLOR = "#10b981"     # 成功绿
WARNING_COLOR = "#f59e0b"     # 警告橙  
ERROR_COLOR = "#ef4444"       # 错误红
INFO_COLOR = "#3b82f6"        # 信息蓝

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

# 基础色
WHITE = "#ffffff"
BLACK = "#000000"

# 背景色
WINDOW_BG = GRAY_50
SIDEBAR_BG = "#1e293b" # 深色侧边栏
SIDEBAR_TEXT = GRAY_200
SIDEBAR_HOVER = "#334155"
SIDEBAR_ACTIVE = PRIMARY_COLOR

# ==========================================
# 2. 字体系统
# ==========================================

FONT_FAMILY = "Segoe UI, Microsoft YaHei, Arial, sans-serif"

# 字体大小 (Int)
FONT_SIZE_XS_INT = 12
FONT_SIZE_SM_INT = 14
FONT_SIZE_BASE_INT = 16
FONT_SIZE_LG_INT = 18
FONT_SIZE_XL_INT = 20
FONT_SIZE_2XL_INT = 24
FONT_SIZE_3XL_INT = 30

# 字体大小 (Str)
FONT_SIZE_XS = f"{FONT_SIZE_XS_INT}px"
FONT_SIZE_SM = f"{FONT_SIZE_SM_INT}px"
FONT_SIZE_BASE = f"{FONT_SIZE_BASE_INT}px"
FONT_SIZE_LG = f"{FONT_SIZE_LG_INT}px"
FONT_SIZE_XL = f"{FONT_SIZE_XL_INT}px"
FONT_SIZE_2XL = f"{FONT_SIZE_2XL_INT}px"
FONT_SIZE_3XL = f"{FONT_SIZE_3XL_INT}px"

# 字重
FONT_WEIGHT_NORMAL = "400"
FONT_WEIGHT_MEDIUM = "500"
FONT_WEIGHT_BOLD = "700"

# ==========================================
# 3. 间距系统
# ==========================================

# 间距单位 (Int)
SPACING_XS_INT = 4
SPACING_SM_INT = 8
SPACING_MD_INT = 12
SPACING_LG_INT = 16
SPACING_XL_INT = 20
SPACING_2XL_INT = 24
SPACING_3XL_INT = 32

# 间距单位 (Str)
SPACING_XS = f"{SPACING_XS_INT}px"
SPACING_SM = f"{SPACING_SM_INT}px"
SPACING_MD = f"{SPACING_MD_INT}px"
SPACING_LG = f"{SPACING_LG_INT}px"
SPACING_XL = f"{SPACING_XL_INT}px"
SPACING_2XL = f"{SPACING_2XL_INT}px"
SPACING_3XL = f"{SPACING_3XL_INT}px"

# ==========================================
# 4. 圆角系统
# ==========================================

RADIUS_SM = "4px"
RADIUS_BASE = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
RADIUS_FULL = "9999px"

# ==========================================
# 5. 边框与阴影
# ==========================================

BORDER_COLOR = GRAY_200
BORDER_WIDTH = "1px"
BORDER_STYLE = f"{BORDER_WIDTH} solid {BORDER_COLOR}"

SHADOW_COLOR = "rgba(0, 0, 0, 0.1)"
TABLE_HOVER_BG = "#eff6ff"      # 表格行 hover 浅蓝背景
TABLE_HEADER_BG = GRAY_50
TABLE_BORDER = GRAY_200
CARD_PADDING = SPACING_XL_INT   # 卡片内边距 20px
EMPTY_STATE_COLOR = GRAY_400
