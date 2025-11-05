"""
티스토리 블로그 작성 모듈 (Selenium 기반)
- 티스토리 Open API 종료로 인해 Selenium 웹 자동화 사용
- 카카오 로그인 → 티스토리 글쓰기 → HTML 삽입 → 발행
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
import re
from typing import List, Dict, Optional


class TistorySeleniumWriter:
    """티스토리 Selenium 자동화 클래스"""

    def __init__(self, kakao_email: str, kakao_password: str, blog_name: str):
        """
        초기화

        Args:
            kakao_email: 카카오 이메일
            kakao_password: 카카오 비밀번호
            blog_name: 티스토리 블로그 이름 (예: 'mylittleshop')
        """
        self.kakao_email = kakao_email
        self.kakao_password = kakao_password
        self.blog_name = blog_name
        self.driver = None
        self.is_logged_in = False

        # 쿠키 저장 경로
        config_dir = os.path.join(os.getenv('APPDATA'), 'ColdAPP')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        self.cookies_file = os.path.join(config_dir, 'tistory_cookies.json')

        # 티스토리 글쓰기 URL
        self.editor_url = f"https://{blog_name}.tistory.com/manage/newpost"

    def _init_driver(self):
        """Chrome 드라이버 초기화"""
        if self.driver:
            return

        print("🔧 Chrome 드라이버 초기화 중...")

        options = uc.ChromeOptions()
        # options.add_argument('--headless')  # 필요시 주석 해제
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
        print("✅ 드라이버 초기화 완료")

    def _save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f)
            print(f"   💾 쿠키 저장 완료: {self.cookies_file}")
        except Exception as e:
            print(f"   ⚠️ 쿠키 저장 실패: {e}")

    def _load_cookies(self) -> bool:
        """쿠키 로드"""
        try:
            if not os.path.exists(self.cookies_file):
                return False

            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            self.driver.get("https://www.tistory.com")
            time.sleep(1)

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass

            print("   ✅ 쿠키 로드 완료")
            return True

        except Exception as e:
            print(f"   ⚠️ 쿠키 로드 실패: {e}")
            return False

    def login(self) -> bool:
        """
        카카오 계정으로 티스토리 로그인

        Returns:
            bool: 로그인 성공 여부
        """
        self._init_driver()

        print("\n🔐 티스토리(카카오) 로그인 시작...")

        try:
            # 쿠키로 로그인 시도
            if self._load_cookies():
                self.driver.get(self.editor_url)
                time.sleep(2)

                # 로그인 상태 확인
                if "manage/newpost" in self.driver.current_url:
                    print("   ✅ 쿠키 로그인 성공!")
                    self.is_logged_in = True
                    return True

            # 쿠키 로그인 실패 시 수동 로그인
            print("   🔑 수동 로그인 시작...")
            self.driver.get("https://www.tistory.com/auth/login")

            # React 앱 로딩 대기 (중요!)
            print("   ⏳ 페이지 로딩 대기 중...")
            time.sleep(3)

            # React 앱이 렌더링될 때까지 대기
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-react-app='loginPagePC']"))
                )
                print("   ✅ React 앱 로딩 완료")
            except:
                print("   ⚠️ React 앱 확인 실패, 계속 진행...")

            # 카카오 로그인 버튼 클릭 (여러 셀렉터 시도 + JavaScript 클릭)
            print("   🔍 카카오 로그인 버튼 찾는 중...")
            kakao_btn = None
            kakao_selectors = [
                # span 텍스트를 직접 찾기 (최우선!)
                (By.XPATH, "//span[@class='txt_login' and contains(text(), '카카오계정으로 로그인')]"),
                (By.CSS_SELECTOR, "span.txt_login"),  # span 직접
                # 부모 a 태그
                (By.CSS_SELECTOR, "a.btn_login.link_kakao_id"),
                (By.CSS_SELECTOR, "a.link_kakao_id"),
                (By.XPATH, "//a[contains(@class, 'link_kakao_id')]"),
            ]

            for selector_type, selector_value in kakao_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"   ✅ 카카오 버튼 요소 찾음: {selector_value}")

                    # span을 찾았으면 부모 a 태그를 클릭해야 함
                    if selector_value.startswith("//span") or "span" in selector_value:
                        # span의 부모 a 태그 찾기
                        try:
                            kakao_btn = element.find_element(By.XPATH, "./ancestor::a[@class='btn_login link_kakao_id']")
                            print(f"   ✅ 부모 a 태그 찾음")
                        except:
                            # 부모를 못 찾으면 element 자체 사용
                            kakao_btn = element
                    else:
                        kakao_btn = element

                    break
                except Exception as e:
                    continue

            if not kakao_btn:
                raise Exception("카카오 로그인 버튼을 찾을 수 없습니다")

            # JavaScript로 클릭 (href="#"이므로 일반 클릭 대신)
            print("   🖱️  카카오 버튼 클릭 중 (JavaScript 방식)...")
            try:
                # 방법 1: JavaScript 클릭
                self.driver.execute_script("arguments[0].click();", kakao_btn)
                print("   ✅ JavaScript 클릭 성공")
            except:
                try:
                    # 방법 2: 일반 클릭
                    kakao_btn.click()
                    print("   ✅ 일반 클릭 성공")
                except:
                    # 방법 3: Actions 클릭
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(self.driver).move_to_element(kakao_btn).click().perform()
                    print("   ✅ Actions 클릭 성공")

            print("   ✅ 카카오 로그인 페이지로 이동 요청 완료")
            time.sleep(4)  # 카카오 페이지 로딩 대기

            # 이메일 입력 (여러 셀렉터 시도)
            print("   📧 이메일 입력 중...")
            email_input = None
            email_selectors = [
                (By.ID, "loginId--1"),  # 기본
                (By.NAME, "loginId"),  # name 속성
                (By.CSS_SELECTOR, "input[type='text']"),  # type=text
                (By.CSS_SELECTOR, "input[placeholder*='이메일']"),  # placeholder
                (By.XPATH, "//input[@type='text' or @name='loginId']")  # XPath 백업
            ]

            for selector_type, selector_value in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"   ✅ 이메일 입력 필드 찾음: {selector_value}")
                    break
                except:
                    continue

            if not email_input:
                raise Exception("이메일 입력 필드를 찾을 수 없습니다")

            email_input.clear()
            email_input.send_keys(self.kakao_email)
            time.sleep(1)

            # 비밀번호 입력 (여러 셀렉터 시도)
            print("   🔒 비밀번호 입력 중...")
            password_input = None
            password_selectors = [
                (By.ID, "password--2"),  # 기본
                (By.NAME, "password"),  # name 속성
                (By.CSS_SELECTOR, "input[type='password']"),  # type=password
                (By.XPATH, "//input[@type='password']")  # XPath 백업
            ]

            for selector_type, selector_value in password_selectors:
                try:
                    password_input = self.driver.find_element(selector_type, selector_value)
                    print(f"   ✅ 비밀번호 입력 필드 찾음: {selector_value}")
                    break
                except:
                    continue

            if not password_input:
                raise Exception("비밀번호 입력 필드를 찾을 수 없습니다")

            password_input.clear()
            password_input.send_keys(self.kakao_password)
            time.sleep(1)

            # 로그인 버튼 클릭 (여러 셀렉터 시도)
            print("   🚀 로그인 버튼 클릭...")
            login_btn = None
            login_selectors = [
                (By.CSS_SELECTOR, "button.btn_g.highlight.submit"),  # 기본
                (By.CSS_SELECTOR, "button[type='submit']"),  # type=submit
                (By.XPATH, "//button[@type='submit']"),  # XPath 백업
                (By.CSS_SELECTOR, "button.submit_btn"),  # 클래스명
            ]

            for selector_type, selector_value in login_selectors:
                try:
                    login_btn = self.driver.find_element(selector_type, selector_value)
                    print(f"   ✅ 로그인 버튼 찾음: {selector_value}")
                    break
                except:
                    continue

            if not login_btn:
                raise Exception("로그인 버튼을 찾을 수 없습니다")

            login_btn.click()

            # 로그인 완료 대기 (최대 15초)
            print("   ⏳ 로그인 처리 중...")
            WebDriverWait(self.driver, 15).until(
                lambda d: "tistory.com" in d.current_url and "auth/login" not in d.current_url
            )

            # 쿠키 저장
            self._save_cookies()

            print("   ✅ 로그인 성공!")
            self.is_logged_in = True
            return True

        except TimeoutException:
            print("   ❌ 로그인 타임아웃")
            return False
        except Exception as e:
            print(f"   ❌ 로그인 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _convert_naver_format_to_html(self, ai_content: str, image_urls: List[str], shopping_url: str) -> str:
        """
        네이버 블로그 형식([TEXT], [IMAGE:1], [LINK])을 티스토리 HTML로 변환

        Args:
            ai_content: AI가 생성한 네이버 형식 콘텐츠
            image_urls: 업로드된 이미지 URL 리스트
            shopping_url: 쇼핑 URL

        Returns:
            str: 티스토리용 HTML
        """
        html_parts = []

        # 순차적으로 파싱
        lines = ai_content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # [TEXT] 섹션
            if line.startswith('[TEXT]'):
                content = line.replace('[TEXT]', '').strip()
                if content:
                    # 줄바꿈을 <br>로 변환
                    content = content.replace('\n', '<br>')
                    html_parts.append(f'<p style="line-height: 1.8; font-size: 16px; color: #333;">{content}</p>')

            # [QUOTE:VERTICAL] - 세로 인용구 (배경색 박스)
            elif line.startswith('[QUOTE:VERTICAL]'):
                content = line.replace('[QUOTE:VERTICAL]', '').strip()
                if content:
                    html_parts.append(f'''
<div style="background: linear-gradient(to right, #667eea 4px, transparent 4px);
            background-color: #f3f4f6;
            padding: 16px 16px 16px 24px;
            margin: 20px 0;
            border-radius: 8px;">
    <p style="font-size: 18px; font-weight: bold; color: #1f2937; margin: 0;">{content}</p>
</div>
''')

            # [QUOTE:UNDERLINE] - 밑줄 인용구 (소제목)
            elif line.startswith('[QUOTE:UNDERLINE]'):
                content = line.replace('[QUOTE:UNDERLINE]', '').strip()
                if content:
                    html_parts.append(f'''
<h3 style="font-size: 20px;
           font-weight: bold;
           color: #1f2937;
           border-bottom: 3px solid #667eea;
           padding-bottom: 8px;
           margin: 24px 0 16px 0;">
    {content}
</h3>
''')

            # [IMAGE:x,y] - 이미지
            elif '[IMAGE:' in line:
                match = re.search(r'\[IMAGE:([\d,]+)\]', line)
                if match:
                    indices = match.group(1).split(',')
                    img_html = '<div style="text-align: center; margin: 20px 0;">'

                    for idx_str in indices:
                        idx = int(idx_str.strip()) - 1  # 1-based → 0-based
                        if 0 <= idx < len(image_urls):
                            img_html += f'<img src="{image_urls[idx]}" alt="Image" style="max-width: 100%; height: auto; margin: 8px;" />'

                    img_html += '</div>'
                    html_parts.append(img_html)

            # [LINK] - 쇼핑 링크
            elif '[LINK]' in line:
                html_parts.append(f'''
<div style="background-color: #eff6ff;
            border: 2px solid #3b82f6;
            border-radius: 12px;
            padding: 16px;
            margin: 24px 0;
            text-align: center;">
    <a href="{shopping_url}"
       target="_blank"
       style="color: #1e40af;
              font-size: 16px;
              font-weight: bold;
              text-decoration: none;">
        🛒 제품 구매하기
    </a>
</div>
''')

        return '\n'.join(html_parts)

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        이미지 업로드 (Selenium 방식)

        Args:
            image_path: 이미지 파일 경로

        Returns:
            str: 업로드된 이미지 URL (실패 시 None)
        """
        print(f"   📤 이미지 업로드: {image_path}")

        try:
            # 첨부 버튼 클릭
            attach_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button#mceu_0-open"))
            )
            attach_btn.click()
            time.sleep(1)

            # 파일 선택 (숨겨진 input[type=file] 찾기)
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(image_path))

            # 업로드 완료 대기
            time.sleep(2)

            # 업로드된 이미지 URL 가져오기 (iframe 내부에서)
            self.driver.switch_to.frame("editor-tistory_ifr")

            # 가장 최근 업로드된 이미지 찾기
            images = self.driver.find_elements(By.TAG_NAME, "img")
            if images:
                image_url = images[-1].get_attribute("src")
                print(f"      ✅ 업로드 완료: {image_url}")
                self.driver.switch_to.default_content()
                return image_url

            self.driver.switch_to.default_content()
            return None

        except Exception as e:
            print(f"      ❌ 이미지 업로드 오류: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return None

    def write_post(
        self,
        title: str,
        ai_result: Dict,
        image_files: List[str],
        shopping_url: str,
        category: str = None
    ) -> bool:
        """
        티스토리에 글 작성 (Selenium 방식)

        Args:
            title: 글 제목
            ai_result: AI 생성 결과 {'content': '...', 'tags': [...]}
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
            category: 카테고리 (선택)

        Returns:
            bool: 성공 여부
        """
        if not self.is_logged_in:
            print("❌ 로그인이 필요합니다.")
            return False

        print(f"\n📝 티스토리 글 작성 중...")
        print(f"   제목: {title}")

        try:
            # 1. 글쓰기 페이지 이동
            self.driver.get(self.editor_url)
            time.sleep(3)

            # 2. 이미지 업로드
            print(f"\n📤 이미지 업로드 중 ({len(image_files)}개)...")
            image_urls = []

            for i, img_path in enumerate(image_files, 1):
                print(f"   [{i}/{len(image_files)}] 업로드 중...")
                url = self.upload_image(img_path)
                if url:
                    image_urls.append(url)
                time.sleep(1)

            print(f"   ✅ {len(image_urls)}개 이미지 업로드 완료")

            # 3. 네이버 형식 → 티스토리 HTML 변환
            print(f"\n🔄 HTML 변환 중...")
            html_content = self._convert_naver_format_to_html(
                ai_result['content'],
                image_urls,
                shopping_url
            )

            # 4. 제목 입력
            print(f"\n✍️ 제목 입력 중...")
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "post-title-inp"))
            )
            title_input.clear()
            title_input.send_keys(title)
            time.sleep(0.5)

            # 5. 본문 입력 (iframe 내부)
            print(f"\n✍️ 본문 입력 중...")

            # iframe으로 전환
            self.driver.switch_to.frame("editor-tistory_ifr")

            # JavaScript로 HTML 삽입
            escaped_html = html_content.replace('`', '\\`').replace('$', '\\$')
            self.driver.execute_script(f"document.body.innerHTML = `{escaped_html}`;")

            # 원래 프레임으로 복귀
            self.driver.switch_to.default_content()
            time.sleep(1)

            # 6. 태그 입력
            print(f"\n🏷️ 태그 입력 중...")
            tags = ai_result.get('tags', [])[:10]  # 최대 10개

            if tags:
                tag_input = self.driver.find_element(By.ID, "tagText")
                for tag in tags:
                    tag_input.send_keys(tag)
                    tag_input.send_keys(Keys.ENTER)
                    time.sleep(0.3)
                print(f"   ✅ {len(tags)}개 태그 입력 완료")

            # 7. 발행 버튼 클릭
            print(f"\n🚀 글 발행 중...")
            publish_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "publish-layer-btn"))
            )
            publish_btn.click()
            time.sleep(2)

            # 발행 확인 팝업 처리 (있다면)
            try:
                confirm_btn = self.driver.find_element(By.CSS_SELECTOR, "button.confirm, button.publish")
                confirm_btn.click()
                time.sleep(2)
            except NoSuchElementException:
                pass

            print(f"\n✅ 티스토리 글 발행 완료!")
            print(f"   URL: https://{self.blog_name}.tistory.com")

            return True

        except Exception as e:
            print(f"\n❌ 티스토리 글 작성 오류: {e}")
            import traceback
            traceback.print_exc()

            # iframe에서 빠져나오기
            try:
                self.driver.switch_to.default_content()
            except:
                pass

            return False

    def close(self):
        """브라우저 종료"""
        if self.driver:
            print("\n🔒 브라우저 종료 중...")
            self.driver.quit()
            self.driver = None
            print("   ✅ 종료 완료")

    def __del__(self):
        """소멸자 - 브라우저 자동 종료"""
        self.close()
