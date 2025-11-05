"""
네이버 블로그 자동화 GUI - Modern Flat Layout (Sidebar + Content)
- 사이드바 내비게이션
- 플랫, 라이트, 균형 잡힌 여백
- 이중 테두리/카드 박스 제거 (책상 느낌 제거)
- 일관된 타이포와 간격 시스템
- Firebase 인증 시스템 통합
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QFrame,
    QStackedWidget, QSizePolicy, QSpacerItem, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
import json
import os
import webbrowser
from naver_blog_automation import NaverBlogAutomation
from firebase_auth import FirebaseAuthManager


class Colors:
    BG = "#F7F8FA"              # 전체 배경
    SURFACE = "#FFFFFF"         # 표면
    DIVIDER = "#E6E8EE"         # 구분선
    PRIMARY = "#4F46E5"         # 인디고
    PRIMARY_DARK = "#4338CA"
    TEXT = "#1F2937"            # 본문
    TEXT_WEAK = "#6B7280"       # 보조
    DANGER = "#EF4444"
    SUCCESS = "#10B981"


class AutomationThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config, shopping_url):
        super().__init__()
        self.config = config
        self.shopping_url = shopping_url
        self.bot = None

    def run(self):
        try:
            self.progress.emit("🌐 브라우저 시작 중...")
            self.bot = NaverBlogAutomation(
                self.config['blog_id'],
                self.config['naver_id'],
                self.config['naver_pw'],
                self.config['gemini_api_key']
            )
            self.bot.start_browser()
            self.progress.emit("✅ 브라우저 시작 완료\n")

            self.progress.emit("🔐 로그인 중...")
            if not self.bot.login():
                self.finished.emit(False, "로그인 실패")
                return
            self.progress.emit("✅ 로그인 완료\n")

            self.progress.emit("📦 제품 정보 추출 중...")
            product_info = self.bot.extract_product_info(self.shopping_url)
            if not product_info:
                self.finished.emit(False, "제품 정보 추출 실패")
                return
            self.progress.emit(f"✅ 제품명: {product_info['title'][:50]}...\n")

            self.progress.emit("💾 이미지 다운로드 중...")
            image_files = self.bot.download_images(product_info['images'])
            if not image_files:
                self.finished.emit(False, "이미지 다운로드 실패 - 최소 1개")
                return
            self.progress.emit(f"✅ {len(image_files)}개 이미지 다운로드 완료\n")

            self.progress.emit("🤖 AI 글 생성 중...")
            ai_result = self.bot.generate_ai_content(product_info)
            if not ai_result:
                self.finished.emit(False, "AI 글 생성 실패")
                return
            self.progress.emit(f"✅ AI 글 생성 완료 ({len(ai_result['content'])}자)\n")
            self.progress.emit(f"✅ 태그 {len(ai_result['tags'])}개 생성\n")

            self.progress.emit("📝 블로그 글 작성 및 발행 중...")
            if self.bot.write_blog_post(product_info['title'], ai_result, image_files, self.shopping_url):
                self.finished.emit(True, "블로그 글 발행 완료! 🎉")
            else:
                self.finished.emit(False, "블로그 글 작성 실패")
        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")
        finally:
            if self.bot:
                self.bot.close()


class LoginDialog(QDialog):
    """Firebase 로그인 다이얼로그"""
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.user_info = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("ColdAPP - 로그인")
        self.setFixedSize(400, 600)  # 높이 대폭 증가 (570 → 600)
        self.setStyleSheet(f"background: {Colors.BG};")
        
        # 윈도우 아이콘 설정 (타이틀바)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 EXE 환경
            window_icon_path = os.path.join(sys._MEIPASS, 'assets', 'coldapp_icon_64x64.png')
        else:
            # 일반 Python 실행 환경
            window_icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'coldapp_icon_64x64.png')
        
        if os.path.exists(window_icon_path):
            self.setWindowIcon(QIcon(window_icon_path))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)  # 상단 여백 증가 (24 → 32)
        layout.setSpacing(10)
        
        # 아이콘 (로그인 창 - 64x64)
        icon_label = QLabel()
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 EXE 환경
            icon_path = os.path.join(sys._MEIPASS, 'assets', 'coldapp_icon_64x64.png')
        else:
            # 일반 Python 실행 환경
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'coldapp_icon_64x64.png')
        
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedHeight(120)  # 훨씬 더 큰 높이 (100 → 120)
        else:
            # 아이콘 못 찾았을 때 대체
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
        
        layout.addSpacing(8)  # 상단 섹션 마무리
        
        # 이메일 입력
        email_label = QLabel("이메일")
        email_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 12px; font-weight: 700;")
        layout.addWidget(email_label)
        
        # 저장된 이메일 불러오기
        saved_email = ConfigManager.load_login_email()
        self.email_input = LineEdit("user@example.com")  # placeholder는 예시로
        if saved_email:
            self.email_input.setText(saved_email)  # 실제 값으로 저장된 이메일 입력
        self.email_input.setFixedHeight(40)
        layout.addWidget(self.email_input)
        
        layout.addSpacing(4)  # 이메일과 비밀번호 사이 작은 여백
        
        # 비밀번호 입력
        pw_label = QLabel("비밀번호")
        pw_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 12px; font-weight: 700;")
        layout.addWidget(pw_label)
        
        self.pw_input = LineEdit("비밀번호")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setFixedHeight(40)
        layout.addWidget(self.pw_input)
        
        layout.addSpacing(14)  # 비밀번호와 로그인 버튼 사이 **늘린 여백**
        
        # 로그인 버튼
        self.login_btn = SolidButton("로그인")
        self.login_btn.clicked.connect(self.try_login)
        self.login_btn.setFixedHeight(44)
        layout.addWidget(self.login_btn)
        
        layout.addSpacing(8)  # 로그인 버튼과 하단 버튼들 사이 간격
        
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
        
        layout.addSpacing(6)  # 버튼과 상태 메시지 사이 작은 여백
        
        # 상태 메시지 (고정 높이 - 오류 메시지 표시 공간)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {Colors.DANGER}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setFixedHeight(40)  # 오류 메시지 공간 (고정)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(8)  # 상태 메시지와 Made by Changong 사이 여백
        
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
                # signup2로 변경된 회원가입 URL
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
                # 홈페이지 URL
                website_url = "https://xn--ob0by50d.store/"
                webbrowser.open(website_url)
        except Exception as e:
            QMessageBox.warning(self, "오류", f"홈페이지를 열 수 없습니다.\n{str(e)}")



class ConfigManager:
    """
    ColdAPP 설정 및 로그인 이메일 저장 관리자
    AppData\Roaming\ColdAPP\config.json 에 저장
    """
    CONFIG_DIR = os.path.join(os.getenv("APPDATA"), "ColdAPP")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    @staticmethod
    def ensure_dir():
        """폴더가 없으면 자동 생성"""
        if not os.path.exists(ConfigManager.CONFIG_DIR):
            os.makedirs(ConfigManager.CONFIG_DIR, exist_ok=True)

    @staticmethod
    def load():
        """설정 파일 불러오기"""
        ConfigManager.ensure_dir()
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # 기본 구조 반환
        return {
            "blog_id": "",
            "naver_id": "",
            "naver_pw": "",
            "gemini_api_key": "",
            "last_login_email": ""
        }

    @staticmethod
    def save(config):
        """설정 파일 저장"""
        ConfigManager.ensure_dir()
        with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def save_login_email(email: str):
        """Firebase 로그인 이메일만 저장"""
        config = ConfigManager.load()
        config["last_login_email"] = email
        ConfigManager.save(config)

    @staticmethod
    def load_login_email() -> str:
        """저장된 Firebase 로그인 이메일 불러오기"""
        config = ConfigManager.load()
        return config.get("last_login_email", "")



class NavButton(QPushButton):
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
    def __init__(self, text, color=Colors.PRIMARY):
        super().__init__(text)
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


class MainWindow(QMainWindow):
    def __init__(self, user_info=None):
        super().__init__()
        self.config = ConfigManager.load()
        self.thread = None
        self.user_info = user_info
        self.auth_manager = FirebaseAuthManager()
        self.init_ui()

    def init_ui(self):
        title = "ColdAPP (Ai Posting Program)"
        if self.user_info:
            title += f" - {self.user_info.get('name', '')}"  # 닉네임 추가
        self.setWindowTitle(title)
        
        # ColdApp 아이콘 설정 (타이틀바 + 작업표시줄)
        # EXE로 빌드했을 때도 작동하도록 경로 처리
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller로 빌드된 EXE 환경
            icon_path = os.path.join(sys._MEIPASS, 'assets', 'coldapp_icon_64x64.png')
        else:
            # 일반 Python 실행 환경
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'coldapp_icon_64x64.png')
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠️ 아이콘 못 찾음: {icon_path}")
        
        self.setMinimumSize(1120, 720)
        root = QWidget()
        root.setStyleSheet(f"background: {Colors.BG};")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        # 사이드바
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background: {Colors.SURFACE}; border: none; border-radius: 12px;")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(8)

        # 아이콘 (사이드바 상단 - 32x32)
        sidebar_icon = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'coldapp_icon_32x32.png')
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            sidebar_icon.setPixmap(icon_pixmap)
            sidebar_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            side_layout.addWidget(sidebar_icon)

        brand = QLabel("ColdAPP")
        brand.setStyleSheet(f"color:{Colors.TEXT}; font-size:18px; font-weight:800;")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(brand)

        sub = QLabel("AI 자동 포스팅")
        sub.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:600;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(sub)

        divider = QFrame(); divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color:{Colors.DIVIDER};")
        side_layout.addWidget(divider)

        self.btn_automation = NavButton("자동 포스팅", True)
        self.btn_settings = NavButton("설정")
        side_layout.addWidget(self.btn_automation)
        side_layout.addWidget(self.btn_settings)
        side_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # 사용자 정보 카드 (왼쪽 아래)
        if self.user_info:
            user_card = QWidget()
            user_card.setStyleSheet(f"""
                background: rgba(102, 126, 234, 0.1);
                border: none;
                border-radius: 12px;
                padding: 12px;
            """)
            user_layout = QVBoxLayout(user_card)
            user_layout.setContentsMargins(10, 10, 10, 10)
            user_layout.setSpacing(4)  # 여백 줄임 (6 → 4)

            # 닉네임
            nickname_label = QLabel(f"👤 {self.user_info.get('name', 'Unknown')}")
            nickname_label.setStyleSheet(f"color: {Colors.TEXT}; font-size: 12px; font-weight: 600;")
            user_layout.addWidget(nickname_label)

            # IP 주소
            signup_ip = self.user_info.get('signupIP', 'N/A')
            if signup_ip == 'unknown':
                signup_ip = '정보 없음'
            ip_label = QLabel(f"🌐 {signup_ip}")
            ip_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 11px;")
            user_layout.addWidget(ip_label)

            # 사용 기간
            expiry_date = self.user_info.get('expiry_date')
            if expiry_date:
                if isinstance(expiry_date, str):
                    days_left = "기간 미정"
                else:
                    from datetime import datetime
                    days_diff = (expiry_date - datetime.now()).days
                    if days_diff < 0:
                        days_left = "만료됨"
                    elif days_diff == 0:
                        days_left = "오늘 만료"
                    else:
                        days_left = f"{days_diff}일 남음"
            else:
                days_left = "무제한"
            
            expiry_label = QLabel(f"📅 {days_left}")
            expiry_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 11px;")
            user_layout.addWidget(expiry_label)
            
            # Made by Changong (카드 맨 아래)
            user_layout.addSpacing(2)  # 작은 여백
            made_by_label = QLabel("Made by Changong")
            made_by_label.setStyleSheet(f"color: {Colors.TEXT_WEAK}; font-size: 9px; font-weight: 500;")
            made_by_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            user_layout.addWidget(made_by_label)

            side_layout.addWidget(user_card)

        # 콘텐츠
        content = QWidget()
        content.setStyleSheet("")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        # 상단 툴바 (플랫)
        toolbar = QWidget();
        # 상단 바는 박스가 아니라 얇은 하단 구분선만
        toolbar.setStyleSheet(f"background:{Colors.SURFACE}; border:none; border-bottom:1px solid {Colors.DIVIDER}; border-radius:12px;")
        bar = QHBoxLayout(toolbar); bar.setContentsMargins(0, 10, 0, 10)
        title = QLabel("📝 자동 포스팅"); title.setStyleSheet(f"color:{Colors.TEXT}; font-size:16px; font-weight:800;")
        bar.addWidget(title)
        bar.addStretch()
        self.start_btn = SolidButton("시작하기")
        self.stop_btn = SolidButton("중지", color=Colors.DANGER)
        self.stop_btn.setEnabled(False)
        bar.addWidget(self.start_btn); bar.addWidget(self.stop_btn)
        content_layout.addWidget(toolbar)

        # 스택
        self.stack = QStackedWidget()
        self.page_automation = self.build_automation_page()
        self.page_settings = self.build_settings_page()
        self.stack.addWidget(self.page_automation)
        self.stack.addWidget(self.page_settings)
        content_layout.addWidget(self.stack)

        # 레이아웃 조합
        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)

        # 이벤트 연결
        self.btn_automation.clicked.connect(lambda: self.switch_page(0))
        self.btn_settings.clicked.connect(lambda: self.switch_page(1))
        self.start_btn.clicked.connect(self.start_automation)
        self.stop_btn.clicked.connect(self.stop_automation)

    def build_group(self, title_text: str) -> QWidget:
        group = QWidget()
        # 카드 박스 느낌 제거: 배경만 두고 테두리는 없앰
        group.setStyleSheet(f"background:{Colors.SURFACE}; border:none; border-radius:12px;")
        lay = QVBoxLayout(group)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(12)
        title = QLabel(title_text)
        # 타이틀 아래에 얇은 구분선을 줘서 섹션만 분리
        title.setStyleSheet(f"color:{Colors.TEXT}; font-weight:800; font-size:14px; padding-bottom:6px; border-bottom:1px solid {Colors.DIVIDER};")
        lay.addWidget(title)
        return group, lay

    def build_automation_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(12)

        # URL 입력
        url_group, url_lay = self.build_group("📦 쇼핑 URL")
        # 안내 라벨
        helper = QLabel("발급받은 브랜드커넥트 URL(naver.me)을 붙여넣으세요.")
        helper.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px;")
        url_lay.addWidget(helper)

        self.url_input = LineEdit("예: https://naver.me/xxxxxx")
        self.url_input.setToolTip("발급받은 브랜드커넥트 URL")
        url_lay.addWidget(self.url_input)
        layout.addWidget(url_group)

        # 진행 상황
        log_group, log_lay = self.build_group("📊 진행 상황")
        self.progress_text = LogText(); self.progress_text.setMinimumHeight(320)
        log_lay.addWidget(self.progress_text)
        layout.addWidget(log_group, 1)
        return page

    def build_settings_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(12)

        acc_group, acc_lay = self.build_group("🔐 네이버 계정")
        # 블로그 ID
        blog_label = QLabel("블로그 ID (주소의 마지막 ID)")
        blog_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        acc_lay.addWidget(blog_label)
        self.blog_id_input = LineEdit("예: blog.naver.com/ColdAPP → ColdAPP")
        self.blog_id_input.setToolTip("블로그 주소의 마지막 부분 (blog.naver.com/여기)")
        self.blog_id_input.setText(self.config.get('blog_id',''))
        acc_lay.addWidget(self.blog_id_input)

        # 네이버 ID
        nid_label = QLabel("네이버 ID (로그인 아이디)")
        nid_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        acc_lay.addWidget(nid_label)
        self.naver_id_input = LineEdit("네이버 아이디")
        self.naver_id_input.setToolTip("네이버 로그인 아이디")
        self.naver_id_input.setText(self.config.get('naver_id',''))
        acc_lay.addWidget(self.naver_id_input)

        # 네이버 비밀번호
        pw_label = QLabel("네이버 비밀번호")
        pw_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        acc_lay.addWidget(pw_label)
        self.naver_pw_input = LineEdit("비밀번호")
        self.naver_pw_input.setToolTip("네이버 로그인 비밀번호")
        self.naver_pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.naver_pw_input.setText(self.config.get('naver_pw',''))
        acc_lay.addWidget(self.naver_pw_input)
        layout.addWidget(acc_group)

        api_group, api_lay = self.build_group("🤖 Gemini API")
        api_hint = QLabel("Google AI Studio에서 발급받은 Gemini API Key를 입력하세요.")
        api_hint.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px;")
        api_lay.addWidget(api_hint)
        self.gemini_key_input = LineEdit("예: AIzaSy... (절대 외부에 공유하지 마세요)")
        self.gemini_key_input.setToolTip("Google AI Studio 발급 키")
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setText(self.config.get('gemini_api_key',''))
        api_lay.addWidget(self.gemini_key_input)
        layout.addWidget(api_group)

        save_bar = QWidget(); save_bar.setStyleSheet(f"background:{Colors.SURFACE}; border:none; border-radius:12px;")
        hb = QHBoxLayout(save_bar); hb.setContentsMargins(12,10,12,10)
        hb.addStretch(); save_btn = SolidButton("설정 저장", color=Colors.SUCCESS); hb.addWidget(save_btn)
        layout.addWidget(save_bar)
        save_btn.clicked.connect(self.save_settings)
        return page

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_automation.setChecked(index == 0)
        self.btn_settings.setChecked(index == 1)

    def start_automation(self):
        url = self.url_input.text().strip()
        if not url or url.startswith("https://naver.me/") is False:
            QMessageBox.warning(self, "입력 오류", "유효한 쇼핑 URL을 입력하세요.")
            return
        if not all([self.blog_id_input.text().strip(), self.naver_id_input.text().strip(), self.naver_pw_input.text(), self.gemini_key_input.text().strip()]):
            QMessageBox.warning(self, "설정 오류", "설정 정보를 모두 입력하세요.")
            return
        
        # Firebase 사용 제한 체크
        if self.user_info and self.auth_manager.is_enabled():
            email = self.user_info.get('email')
            if not self.auth_manager.check_usage_limit(email):
                QMessageBox.warning(
                    self, 
                    "사용 제한", 
                    f"월 사용 제한에 도달했습니다.\n"
                    f"사용 횟수: {self.user_info.get('usage_count', 0)} / {self.user_info.get('usage_limit', 0)}"
                )
                return

        self.progress_text.clear()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.url_input.setEnabled(False)

        cfg = {
            'blog_id': self.blog_id_input.text().strip(),
            'naver_id': self.naver_id_input.text().strip(),
            'naver_pw': self.naver_pw_input.text(),
            'gemini_api_key': self.gemini_key_input.text().strip()
        }
        self.thread = AutomationThread(cfg, url)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.automation_finished)
        self.thread.start()

    def stop_automation(self):
        if self.thread:
            self.thread.terminate()
            self.automation_finished(False, "사용자가 중지했습니다.")

    def update_progress(self, msg: str):
        self.progress_text.append(msg)

    def automation_finished(self, success: bool, message: str):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.url_input.setEnabled(True)
        
        # Firebase 사용 횟수 증가
        if success and self.user_info and self.auth_manager.is_enabled():
            self.auth_manager.increment_usage(self.user_info.get('email'))
            self.user_info['usage_count'] = self.user_info.get('usage_count', 0) + 1
        
        if success:
            self.progress_text.append(f"\n✅ {message}")
            QMessageBox.information(self, "완료", message)
        else:
            self.progress_text.append(f"\n❌ {message}")
            QMessageBox.warning(self, "실패", message)

    def save_settings(self):
        # 1. 기존 설정을 불러옵니다.
        current_config = ConfigManager.load()
        
        # 2. UI의 값으로 설정을 업데이트합니다.
        current_config['blog_id'] = self.blog_id_input.text().strip()
        current_config['naver_id'] = self.naver_id_input.text().strip()
        current_config['naver_pw'] = self.naver_pw_input.text()
        current_config['gemini_api_key'] = self.gemini_key_input.text().strip()
        
        # 3. 업데이트된 전체 설정을 저장합니다.
        ConfigManager.save(current_config)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다! ✅")


def main():
    # Windows 작업표시줄 아이콘 설정 (중요!)
    if sys.platform == 'win32':
        try:
            import ctypes
            # Windows AppUserModelID 설정 - 작업표시줄에서 올바른 아이콘 표시
            myappid = 'coldapp.autoposting.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    
    app = QApplication(sys.argv)
    app.setFont(QFont("맑은 고딕", 10))
    
    # Firebase 인증 매니저 초기화
    auth_manager = FirebaseAuthManager()
    
    # 로그인 다이얼로그 표시
    login_dialog = LoginDialog(auth_manager)
    
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        user_info = login_dialog.user_info
        w = MainWindow(user_info)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
