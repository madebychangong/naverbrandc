"""
재사용 가능한 GUI 컴포넌트
- 색상 팔레트
- 커스텀 버튼 (네비게이션, 솔리드)
- 커스텀 입력창
- 로그 텍스트
"""

from PyQt6.QtWidgets import QPushButton, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt


class Colors:
    """ColdAPP 색상 팔레트"""
    BG = "#F7F8FA"              # 전체 배경
    SURFACE = "#FFFFFF"         # 표면
    DIVIDER = "#E6E8EE"         # 구분선
    PRIMARY = "#4F46E5"         # 인디고
    PRIMARY_DARK = "#4338CA"
    TEXT = "#1F2937"            # 본문
    TEXT_WEAK = "#6B7280"       # 보조
    DANGER = "#EF4444"
    SUCCESS = "#10B981"


class NavButton(QPushButton):
    """사이드바 네비게이션 버튼"""

    def __init__(self, text, active=False):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setCheckable(True)
        self.setChecked(active)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 0 14px;
                border: none;
                border-radius: 12px;
                background: transparent;
                color: {Colors.TEXT_WEAK};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #EEF2FF;
                color: {Colors.PRIMARY};
            }}
            QPushButton:checked {{
                background: #EEF2FF;
                color: {Colors.PRIMARY};
            }}
        """)


class SolidButton(QPushButton):
    """솔리드 배경 버튼 (Primary, Success, Danger)"""

    def __init__(self, text, color=None):
        super().__init__(text)
        if color is None:
            color = Colors.PRIMARY
        self.color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self.color};
                color: white; border: none; border-radius: 12px;
                font-weight: 700; padding: 0 18px;
            }}
            QPushButton:hover {{ background: {Colors.PRIMARY_DARK}; }}
            QPushButton:disabled {{ background: #CBD5E1; color: white; }}
        """)


class LineEdit(QLineEdit):
    """커스텀 입력창 (Placeholder 지원)"""

    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 0 12px;
                color: {Colors.TEXT};
            }}
            QLineEdit:focus {{
                background: {Colors.SURFACE};
                border: 2px solid {Colors.PRIMARY};
            }}
        """)


class LogText(QTextEdit):
    """읽기 전용 로그 텍스트 에리어"""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px;
                color: {Colors.TEXT};
            }}
        """)
