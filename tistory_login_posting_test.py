"""
티스토리 로그인 및 포스팅 테스트
로그인 후 글쓰기 페이지로 이동하여 테스트 포스팅 작성
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

class TistoryLoginPostingTest:
    def __init__(self, blog_name, email, password):
        """
        티스토리 자동화 초기화
        :param blog_name: 티스토리 블로그 이름 (예: myblog)
        :param email: 카카오 계정 이메일
        :param password: 카카오 계정 비밀번호
        """
        self.blog_name = blog_name
        self.email = email
        self.password = password
        self.driver = None

    def setup_driver(self):
        """웹드라이버 설정"""
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # 헤드리스 모드 (필요시 주석 해제)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

    def login(self):
        """티스토리 로그인 (카카오 계정)"""
        print("티스토리 로그인 시작...")

        # 티스토리 로그인 페이지로 이동
        self.driver.get('https://www.tistory.com/auth/login')
        time.sleep(2)

        try:
            # 카카오 로그인 버튼 클릭
            kakao_login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.btn_login[href*="kakao"]'))
            )
            kakao_login_btn.click()
            print("카카오 로그인 버튼 클릭")
            time.sleep(2)

            # 카카오 로그인 창으로 전환
            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="loginKey"]'))
            )
            email_input.clear()
            email_input.send_keys(self.email)
            print(f"이메일 입력: {self.email}")
            time.sleep(1)

            # 비밀번호 입력
            password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
            password_input.clear()
            password_input.send_keys(self.password)
            print("비밀번호 입력 완료")
            time.sleep(1)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_btn.click()
            print("로그인 버튼 클릭")
            time.sleep(3)

            # 로그인 성공 확인
            WebDriverWait(self.driver, 10).until(
                lambda driver: 'tistory.com' in driver.current_url
            )
            print("✓ 로그인 성공!")
            return True

        except Exception as e:
            print(f"✗ 로그인 실패: {str(e)}")
            return False

    def write_post(self, title, content):
        """
        글쓰기
        :param title: 포스트 제목
        :param content: 포스트 내용
        """
        print("\n글쓰기 시작...")

        try:
            # 글쓰기 페이지로 이동
            write_url = f'https://{self.blog_name}.tistory.com/manage/newpost/'
            self.driver.get(write_url)
            print(f"글쓰기 페이지 접속: {write_url}")
            time.sleep(3)

            # 제목 입력
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="제목"], input.title, #title'))
            )
            title_input.clear()
            title_input.send_keys(title)
            print(f"제목 입력: {title}")
            time.sleep(1)

            # 본문 입력 (에디터 타입에 따라 다를 수 있음)
            # 일반 에디터
            try:
                # iframe으로 전환 필요할 수 있음
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                if iframes:
                    self.driver.switch_to.frame(iframes[0])

                content_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'body[contenteditable], .editor, #content'))
                )
                content_input.clear()
                content_input.send_keys(content)
                print(f"내용 입력: {content}")

                # 원래 컨텍스트로 돌아가기
                self.driver.switch_to.default_content()

            except:
                # iframe이 없는 경우
                self.driver.switch_to.default_content()
                content_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[placeholder*="내용"], textarea.content, #content'))
                )
                content_input.clear()
                content_input.send_keys(content)
                print(f"내용 입력: {content}")

            time.sleep(2)

            # 발행 버튼 클릭
            publish_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="publish"], button.btn_publish, button:contains("발행")'))
            )
            publish_btn.click()
            print("발행 버튼 클릭")
            time.sleep(2)

            # 발행 확인 (팝업이 있을 수 있음)
            try:
                confirm_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="confirm"], button.btn_confirm'))
                )
                confirm_btn.click()
                print("발행 확인 버튼 클릭")
            except:
                print("확인 버튼 없음 (바로 발행)")

            time.sleep(3)
            print("✓ 포스팅 성공!")
            return True

        except Exception as e:
            print(f"✗ 포스팅 실패: {str(e)}")
            self.driver.save_screenshot('error_screenshot.png')
            print("에러 스크린샷 저장: error_screenshot.png")
            return False

    def run_test(self):
        """전체 테스트 실행"""
        try:
            print("="*50)
            print("티스토리 로그인 및 포스팅 테스트 시작")
            print("="*50)

            # 웹드라이버 설정
            self.setup_driver()

            # 로그인
            if not self.login():
                print("로그인 실패로 테스트 중단")
                return False

            # 글쓰기
            if not self.write_post("테스트", "테스트"):
                print("포스팅 실패")
                return False

            print("\n" + "="*50)
            print("✓ 모든 테스트 완료!")
            print("="*50)

            # 5초 대기 후 종료
            time.sleep(5)
            return True

        except Exception as e:
            print(f"\n✗ 테스트 중 오류 발생: {str(e)}")
            return False

        finally:
            if self.driver:
                self.driver.quit()
                print("\n브라우저 종료")

def main():
    """메인 함수"""
    # 설정 값 입력
    BLOG_NAME = "your-blog-name"  # 티스토리 블로그 이름 (예: myblog)
    EMAIL = "your-email@kakao.com"  # 카카오 계정 이메일
    PASSWORD = "your-password"  # 카카오 계정 비밀번호

    # 테스트 실행
    test = TistoryLoginPostingTest(BLOG_NAME, EMAIL, PASSWORD)
    test.run_test()

if __name__ == "__main__":
    main()
