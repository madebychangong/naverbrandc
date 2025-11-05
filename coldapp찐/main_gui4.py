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
    QStackedWidget, QSizePolicy, QSpacerItem, QCheckBox, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
import os
from naver_blog_automation import NaverBlogAutomation
from firebase_auth import FirebaseAuthManager
from modules.blog_writer_tistory_selenium import TistorySeleniumWriter
from modules.multi_blog_manager import MultiBlogManager
from gui import Colors, NavButton, SolidButton, LineEdit, LogText, ConfigManager, LoginDialog


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
            use_naver = self.config.get('use_naver', True)
            use_tistory = self.config.get('use_tistory', False)

            if not use_naver and not use_tistory:
                self.finished.emit(False, "포스팅할 블로그를 최소 1개 선택하세요")
                return

            # 공통: 콘텐츠 생성을 위한 변수
            product_info = None
            image_files = None
            ai_result = None

            # 1. 네이버 사용 시 (기존 방식)
            if use_naver:
                self.progress.emit("🌐 브라우저 시작 중...")
                self.bot = NaverBlogAutomation(
                    self.config['blog_id'],
                    self.config['naver_id'],
                    self.config['naver_pw'],
                    self.config['gemini_api_key']
                )
                self.bot.start_browser()
                self.progress.emit("✅ 브라우저 시작 완료\n")

                self.progress.emit("🔐 네이버 로그인 중...")
                if not self.bot.login():
                    self.finished.emit(False, "네이버 로그인 실패")
                    return
                self.progress.emit("✅ 네이버 로그인 완료\n")

                # 제품 정보 추출
                self.progress.emit("📦 제품 정보 추출 중...")
                product_info = self.bot.extract_product_info(self.shopping_url)
                if not product_info:
                    self.finished.emit(False, "제품 정보 추출 실패")
                    return
                self.progress.emit(f"✅ 제품명: {product_info['title'][:50]}...\n")

                # 이미지 다운로드
                self.progress.emit("💾 이미지 다운로드 중...")
                image_files = self.bot.download_images(product_info['images'])
                if not image_files:
                    self.finished.emit(False, "이미지 다운로드 실패 - 최소 1개")
                    return
                self.progress.emit(f"✅ {len(image_files)}개 이미지 다운로드 완료\n")

                # AI 글 생성
                self.progress.emit("🤖 AI 글 생성 중...")
                ai_result = self.bot.generate_ai_content(product_info)
                if not ai_result:
                    self.finished.emit(False, "AI 글 생성 실패")
                    return
                self.progress.emit(f"✅ AI 글 생성 완료 ({len(ai_result['content'])}자)\n")
                self.progress.emit(f"✅ 태그 {len(ai_result['tags'])}개 생성\n")

            # 2. 티스토리만 사용하는 경우 (독립 실행) ⭐ 수정: 로그인 먼저!
            elif use_tistory and not use_naver:
                self.progress.emit("🌐 티스토리 전용 모드 시작\n")

                # 독립 모듈들 import
                from modules.product_extractor import ProductExtractor
                from modules.image_handler import ImageHandler
                from modules.ai_generator import AIContentGenerator

                # 1. 티스토리 로그인 먼저! (네이버처럼)
                tistory_email = self.config.get('tistory_kakao_email', '').strip()
                tistory_password = self.config.get('tistory_kakao_password', '').strip()
                tistory_blog = self.config.get('tistory_blog_name', '').strip()

                if not tistory_email or not tistory_password or not tistory_blog:
                    self.finished.emit(False, "티스토리 설정 정보가 없습니다")
                    return

                self.progress.emit("🔐 티스토리 로그인 중...")
                tistory_writer = TistorySeleniumWriter(
                    kakao_email=tistory_email,
                    kakao_password=tistory_password,
                    blog_name=tistory_blog
                )

                if not tistory_writer.login():
                    self.finished.emit(False, "티스토리 로그인 실패")
                    return
                self.progress.emit("✅ 티스토리 로그인 완료\n")

                # bot 객체 설정 (finally에서 close하기 위해)
                self.bot = tistory_writer

                # 2. 같은 브라우저로 제품 정보 추출
                self.progress.emit("📦 제품 정보 추출 중...")
                extractor = ProductExtractor(tistory_writer.driver)  # 같은 드라이버 사용!
                product_info = extractor.extract_product_info(self.shopping_url)
                if not product_info:
                    self.finished.emit(False, "제품 정보 추출 실패")
                    return
                self.progress.emit(f"✅ 제품명: {product_info['title'][:50]}...\n")

                # 3. 이미지 다운로드
                self.progress.emit("💾 이미지 다운로드 중...")
                img_handler = ImageHandler()
                image_files = img_handler.download_product_images(product_info['images'])
                detail_images = img_handler.download_detail_images(product_info.get('detail_images', []))
                if not image_files:
                    self.finished.emit(False, "이미지 다운로드 실패 - 최소 1개")
                    return
                self.progress.emit(f"✅ {len(image_files)}개 이미지 다운로드 완료\n")

                # 4. AI 글 생성
                self.progress.emit("🤖 AI 글 생성 중...")
                ai_gen = AIContentGenerator(self.config['gemini_api_key'])
                ai_result = ai_gen.generate_content_with_vision(product_info, detail_images)
                if not ai_result:
                    self.finished.emit(False, "AI 글 생성 실패")
                    return
                self.progress.emit(f"✅ AI 글 생성 완료 ({len(ai_result['content'])}자)\n")
                self.progress.emit(f"✅ 태그 {len(ai_result['tags'])}개 생성\n")

            # 5. 멀티 블로그 포스팅
            self.progress.emit("\n" + "="*50)
            self.progress.emit("🚀 멀티 블로그 포스팅 시작")
            self.progress.emit("="*50 + "\n")

            multi_manager = MultiBlogManager()

            # 네이버 작성자 준비
            naver_writer = None
            if use_naver:
                from modules.blog_writer import BlogWriter
                naver_writer = BlogWriter(self.bot.driver)

            # 티스토리 작성자 준비 (Selenium 방식)
            # 주의: 티스토리 단독 모드에서는 이미 tistory_writer가 생성되어 있음!
            if use_tistory and use_naver:
                # 네이버+티스토리 동시 모드: 새로 생성
                tistory_email = self.config.get('tistory_kakao_email', '').strip()
                tistory_password = self.config.get('tistory_kakao_password', '').strip()
                tistory_blog = self.config.get('tistory_blog_name', '').strip()

                if not tistory_email or not tistory_password or not tistory_blog:
                    self.progress.emit("⚠️ 티스토리 설정이 없어 건너뜁니다\n")
                    tistory_writer = None
                else:
                    tistory_writer = TistorySeleniumWriter(
                        kakao_email=tistory_email,
                        kakao_password=tistory_password,
                        blog_name=tistory_blog
                    )
                    # 로그인
                    self.progress.emit("🔗 티스토리 로그인 중...")
                    if not tistory_writer.login():
                        self.progress.emit("⚠️ 티스토리 로그인 실패 - 건너뜁니다\n")
                        tistory_writer = None
                    else:
                        self.progress.emit("✅ 티스토리 로그인 성공\n")
            elif use_tistory and not use_naver:
                # 티스토리 단독 모드: 이미 생성됨, 재사용
                self.progress.emit("✅ 티스토리 writer 재사용\n")
                # tistory_writer는 이미 위에서 생성되어 있음
            else:
                tistory_writer = None

            # 멀티 블로그 포스팅 실행
            results = multi_manager.post_to_multiple_blogs(
                title=product_info['title'],
                ai_result=ai_result,
                image_files=image_files,
                shopping_url=self.shopping_url,
                naver_writer=naver_writer,
                tistory_writer=tistory_writer,
                blog_id=self.config.get('blog_id', '')  # 티스토리 단독 시 빈 문자열
            )

            # 결과 확인
            success_count = sum(1 for r in results.values() if r['success'])

            if success_count > 0:
                summary = multi_manager.get_summary()
                self.finished.emit(True, f"포스팅 완료! 🎉\n\n{summary}")
            else:
                self.finished.emit(False, "모든 블로그 포스팅 실패")

        except Exception as e:
            self.finished.emit(False, f"오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            if self.bot:
                self.bot.close()


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

        self.btn_automation = NavButton("📝 자동 포스팅", True)
        self.btn_naver_settings = NavButton("⚙️ 네이버 설정")
        self.btn_tistory_settings = NavButton("📘 티스토리 설정")
        side_layout.addWidget(self.btn_automation)
        side_layout.addWidget(self.btn_naver_settings)
        side_layout.addWidget(self.btn_tistory_settings)
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
        self.page_naver_settings = self.build_naver_settings_page()
        self.page_tistory_settings = self.build_tistory_settings_page()
        self.stack.addWidget(self.page_automation)
        self.stack.addWidget(self.page_naver_settings)
        self.stack.addWidget(self.page_tistory_settings)
        content_layout.addWidget(self.stack)

        # 레이아웃 조합
        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)

        # 이벤트 연결
        self.btn_automation.clicked.connect(lambda: self.switch_page(0))
        self.btn_naver_settings.clicked.connect(lambda: self.switch_page(1))
        self.btn_tistory_settings.clicked.connect(lambda: self.switch_page(2))
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

    def build_naver_settings_page(self) -> QWidget:
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

        # 네이버 포스팅 활성화
        naver_select_group, naver_select_lay = self.build_group("✅ 네이버 포스팅 활성화")
        self.use_naver_checkbox = QCheckBox("네이버 블로그 포스팅 사용")
        self.use_naver_checkbox.setChecked(self.config.get('use_naver', True))
        self.use_naver_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT};
                font-size: 14px;
                font-weight: 600;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border: 2px solid #D1D5DB;
                border-radius: 6px;
                background: white;
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {Colors.PRIMARY};
                background: #EEF2FF;
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgOEw2LjUgMTEuNUwxMyA0LjUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
        """)
        naver_select_lay.addWidget(self.use_naver_checkbox)
        layout.addWidget(naver_select_group)

        save_bar = QWidget(); save_bar.setStyleSheet(f"background:{Colors.SURFACE}; border:none; border-radius:12px;")
        hb = QHBoxLayout(save_bar); hb.setContentsMargins(12,10,12,10)
        hb.addStretch(); save_btn = SolidButton("설정 저장", color=Colors.SUCCESS); hb.addWidget(save_btn)
        layout.addWidget(save_bar)
        save_btn.clicked.connect(self.save_settings)
        return page

    def build_tistory_settings_page(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(12)

        # 티스토리 설정 안내
        info_group, info_lay = self.build_group("📘 티스토리 설정")
        info_text = QLabel(티스토리는 카카오이메일로 가입 가능합니다.)
        info_text.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; line-height:1.6;")
        info_text.setWordWrap(True)
        info_lay.addWidget(info_text)
        layout.addWidget(info_group)

        # 티스토리 블로그 설정
        tistory_group, tistory_lay = self.build_group("🌐 티스토리 블로그")

        # 블로그 이름
        tistory_blog_label = QLabel("블로그 이름 (예: myblog.tistory.com → myblog)")
        tistory_blog_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        tistory_lay.addWidget(tistory_blog_label)
        self.tistory_blog_input = LineEdit("티스토리 블로그 이름")
        self.tistory_blog_input.setToolTip("티스토리 주소의 앞부분 (예: myblog)")
        self.tistory_blog_input.setText(self.config.get('tistory_blog_name',''))
        tistory_lay.addWidget(self.tistory_blog_input)

        # 카카오 이메일
        tistory_email_label = QLabel("카카오 이메일")
        tistory_email_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        tistory_lay.addWidget(tistory_email_label)
        self.tistory_email_input = LineEdit("카카오 이메일")
        self.tistory_email_input.setToolTip("카카오 계정 이메일")
        self.tistory_email_input.setText(self.config.get('tistory_kakao_email',''))
        tistory_lay.addWidget(self.tistory_email_input)

        # 카카오 비밀번호
        tistory_password_label = QLabel("카카오 비밀번호")
        tistory_password_label.setStyleSheet(f"color:{Colors.TEXT_WEAK}; font-size:12px; font-weight:700;")
        tistory_lay.addWidget(tistory_password_label)
        self.tistory_password_input = LineEdit("카카오 비밀번호")
        self.tistory_password_input.setToolTip("카카오 계정 비밀번호")
        self.tistory_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tistory_password_input.setText(self.config.get('tistory_kakao_password',''))
        tistory_lay.addWidget(self.tistory_password_input)

        # API 종료 안내
        api_notice = QLabel("ℹ️ OPEN AI 설정은 네이버 설정에 있습니다.")
        api_notice.setStyleSheet(f"color:{Colors.PRIMARY}; font-size:11px; padding:8px; background:{Colors.BG}; border:1px solid {Colors.DIVIDER}; border-radius:4px;")
        api_notice.setWordWrap(True)
        tistory_lay.addWidget(api_notice)
        layout.addWidget(tistory_group)

        # 티스토리 포스팅 활성화
        tistory_select_group, tistory_select_lay = self.build_group("✅ 티스토리 포스팅 활성화")
        self.use_tistory_checkbox = QCheckBox("티스토리 포스팅 사용")
        self.use_tistory_checkbox.setChecked(self.config.get('use_tistory', False))
        self.use_tistory_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT};
                font-size: 14px;
                font-weight: 600;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border: 2px solid #D1D5DB;
                border-radius: 6px;
                background: white;
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {Colors.PRIMARY};
                background: #EEF2FF;
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgOEw2LjUgMTEuNUwxMyA0LjUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
        """)
        tistory_select_lay.addWidget(self.use_tistory_checkbox)
        layout.addWidget(tistory_select_group)

        save_bar = QWidget(); save_bar.setStyleSheet(f"background:{Colors.SURFACE}; border:none; border-radius:12px;")
        hb = QHBoxLayout(save_bar); hb.setContentsMargins(12,10,12,10)
        hb.addStretch(); save_btn = SolidButton("설정 저장", color=Colors.SUCCESS); hb.addWidget(save_btn)
        layout.addWidget(save_bar)
        save_btn.clicked.connect(self.save_settings)
        return page

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.btn_automation.setChecked(index == 0)
        self.btn_naver_settings.setChecked(index == 1)
        self.btn_tistory_settings.setChecked(index == 2)

    def start_automation(self):
        url = self.url_input.text().strip()
        if not url or url.startswith("https://naver.me/") is False:
            QMessageBox.warning(self, "입력 오류", "유효한 쇼핑 URL을 입력하세요.")
            return

        # 블로그 선택 확인
        use_naver = self.use_naver_checkbox.isChecked()
        use_tistory = self.use_tistory_checkbox.isChecked()

        if not use_naver and not use_tistory:
            QMessageBox.warning(self, "블로그 선택", "포스팅할 블로그를 최소 1개 선택하세요.")
            return

        # 네이버 설정 검증
        if use_naver:
            if not all([self.blog_id_input.text().strip(), self.naver_id_input.text().strip(),
                       self.naver_pw_input.text(), self.gemini_key_input.text().strip()]):
                QMessageBox.warning(self, "설정 오류", "네이버 블로그 설정 정보를 모두 입력하세요.")
                return

        # 티스토리 설정 검증
        if use_tistory:
            if not all([self.tistory_blog_input.text().strip(),
                       self.tistory_email_input.text().strip(),
                       self.tistory_password_input.text().strip()]):
                reply = QMessageBox.question(
                    self,
                    "티스토리 설정",
                    "티스토리 설정이 완료되지 않았습니다.\n네이버만 포스팅하시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    use_tistory = False
                    self.use_tistory_checkbox.setChecked(False)
                else:
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
            'gemini_api_key': self.gemini_key_input.text().strip(),
            'tistory_blog_name': self.tistory_blog_input.text().strip(),
            'tistory_kakao_email': self.tistory_email_input.text().strip(),
            'tistory_kakao_password': self.tistory_password_input.text().strip(),
            'use_naver': use_naver,
            'use_tistory': use_tistory
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
        current_config['tistory_blog_name'] = self.tistory_blog_input.text().strip()
        current_config['tistory_kakao_email'] = self.tistory_email_input.text().strip()
        current_config['tistory_kakao_password'] = self.tistory_password_input.text().strip()
        current_config['use_naver'] = self.use_naver_checkbox.isChecked()
        current_config['use_tistory'] = self.use_tistory_checkbox.isChecked()

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
