"""
GUI 다이얼로그
- Firebase 로그인 다이얼로그
"""

import sys
import os
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from .components import Colors, SolidButton, LineEdit
from .config_manager import ConfigManager


class LoginDialog(QDialog):
    """Firebase 로그인 다이얼로그"""

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.user_info = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ColdAPP - 로그인")
        self.setFixedSize(400, 600)
        self.setStyleSheet(f"background: {Colors.BG};")

        # 윈도우 아이콘 설정 (타이틀바)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 EXE 환경
            window_icon_path = os.path.join(sys._MEIPASS, 'assets', 'coldapp_icon_64x64.png')
        else:
            # 일반 Python 실행 환경
            window_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'coldapp_icon_64x64.png')

        if os.path.exists(window_icon_path):
            self.setWindowIcon(QIcon(window_icon_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(10)

        # 아이콘 (로그인 창 - 64x64)
        icon_label = QLabel()
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 EXE 환경
            icon_path = os.path.join(sys._MEIPASS, 'assets', 'coldapp_icon_64x64.png')
        else:
            # 일반 Python 실행 환경
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'coldapp_icon_64x64.png')

        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedHeight(120)
        else:
            print(f"⚠️ 아이콘 못 찾음: {icon_path}")

        layout.addWidget(icon_label)

        # 타이틀
        title = QLabel("ColdAPP")
        title.setStyleSheet(f"color: {Colors.TEXT}; font-size: 24px; font-weight: 800;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("AI 자동 포스팅")
        subtitle.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 14px; font-weight: 600;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 이메일 입력
        email_label = QLabel("이메일")
        email_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 12px; font-weight: 700;")
        layout.addWidget(email_label)

        # 저장된 이메일 불러오기
        saved_email = ConfigManager.load_login_email()
        self.email_input = LineEdit("user@example.com")
        if saved_email:
            self.email_input.setText(saved_email)
        self.email_input.setFixedHeight(40)
        layout.addWidget(self.email_input)

        layout.addSpacing(4)

        # 비밀번호 입력
        pw_label = QLabel("비밀번호")
        pw_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 12px; font-weight: 700;")
        layout.addWidget(pw_label)

        self.pw_input = LineEdit("비밀번호")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setFixedHeight(40)
        layout.addWidget(self.pw_input)

        layout.addSpacing(14)

        # 로그인 버튼
        self.login_btn = SolidButton("로그인")
        self.login_btn.clicked.connect(self.try_login)
        self.login_btn.setFixedHeight(44)
        layout.addWidget(self.login_btn)

        layout.addSpacing(8)

        # 하단 버튼들을 가로로 배치
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.setSpacing(8)

        # 회원가입 버튼 (왼쪽)
        self.signup_btn = QPushButton("회원가입")
        self.signup_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                border-radius: 8px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """)
        self.signup_btn.setFixedHeight(38)
        self.signup_btn.clicked.connect(self.do_signup)
        bottom_button_layout.addWidget(self.signup_btn)

        # 문의 버튼 (오른쪽)
        self.inquiry_btn = QPushButton("관리자 문의")
        self.inquiry_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.PRIMARY};
                border: 1px solid {Colors.PRIMARY};
                border-radius: 8px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """)
        self.inquiry_btn.setFixedHeight(38)
        self.inquiry_btn.clicked.connect(self.open_inquiry)
        bottom_button_layout.addWidget(self.inquiry_btn)

        layout.addLayout(bottom_button_layout)

        layout.addSpacing(6)

        # 상태 메시지 (고정 높이 - 오류 메시지 표시 공간)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Colors.DANGER}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(40)
        layout.addWidget(self.status_label)

        layout.addSpacing(8)

        # Made by Changong (하단 정중앙)
        made_by_label = QLabel("Made by Changong")
        made_by_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 10px; font-weight: 500;")
        made_by_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(made_by_label)

    def try_login(self):
        email = self.email_input.text().strip()
        password = self.pw_input.text()

        if not email or not password:
            self.status_label.setText("이메일과 비밀번호를 입력하세요.")
            return

        if not self.auth_manager.is_enabled():
            self.status_label.setText("⚠️ Firebase가 비활성화되어 있습니다.\n계속 진행할 수 없습니다.")
            return

        result = self.auth_manager.verify_user(email, password)

        if 'error' in result:
            self.status_label.setText(result['error'])
        else:
            self.user_info = result
            # 로그인 성공 시 이메일 저장
            ConfigManager.save_login_email(email)
            self.accept()

    def do_signup(self):
        """회원가입 - 웹페이지로 연결"""
        try:
            reply = QMessageBox.question(
                self,
                "회원가입",
                "회원가입 페이지로 이동하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                signup_url = "https://xn--ob0by50d.store/signup2"
                webbrowser.open(signup_url)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"회원가입 페이지를 열 수 없습니다.\n{str(e)}")

    def open_inquiry(self):
        """관리자 문의 - 홈페이지로 연결"""
        try:
            reply = QMessageBox.question(
                self,
                "관리자 문의",
                "홈페이지로 이동하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                website_url = "https://xn--ob0by50d.store/"
                webbrowser.open(website_url)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"홈페이지를 열 수 없습니다.\n{str(e)}")
