"""
브라우저 핸들러 모듈
- 네이버 로그인
- 쿠키 저장/로드
- 캡차 처리 (Gemini Vision)
"""

import time
import os
import json
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class BrowserHandler:
    """브라우저 관련 작업 처리 클래스"""
    
    def __init__(self, driver, naver_id, naver_pw, cookies_file, gemini_api_key):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver
            naver_id: 네이버 ID
            naver_pw: 네이버 비밀번호
            cookies_file: 쿠키 파일 경로
            gemini_api_key: Gemini API 키 (캡차 해결용)
        """
        self.driver = driver
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.cookies_file = cookies_file
        self.gemini_api_key = gemini_api_key
    
    def login(self):
        """네이버 로그인"""
        print("\n🔐 네이버 로그인...")
        
        # 쿠키로 로그인 시도
        if self.load_cookies():
            self.driver.get('https://www.naver.com')
            time.sleep(2)
            
            if 'blog.naver.com' in self.driver.current_url or 'NID_AUT' in self.driver.page_source:
                print("✅ 쿠키 로그인 성공!")
                return True
            else:
                print("⚠️ 쿠키 만료, 재로그인 필요")
        
        # 네이버 로그인 페이지
        self.driver.get('https://nid.naver.com/nidlogin.login')
        time.sleep(3)
        
        # 자동 로그인 시도
        try:
            id_input = self.driver.find_element(By.ID, 'id')
            id_input.click()
            time.sleep(0.8)
            
            pyperclip.copy(self.naver_id)
            id_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(1.5)
            
            pw_input = self.driver.find_element(By.ID, 'pw')
            pw_input.click()
            time.sleep(0.8)
            
            pyperclip.copy(self.naver_pw)
            pw_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(1.5)
            
            login_btn = self.driver.find_element(By.ID, 'log.login')
            login_btn.click()
            time.sleep(5)
            
            current_url = self.driver.current_url
            if 'nid.naver.com' not in current_url:
                print("✅ 자동 로그인 성공!")
                self.save_cookies()
                return True
            else:
                # 캡차 확인
                if self.check_and_solve_captcha():
                    print("✅ 캡차 해결 후 로그인 성공!")
                    self.save_cookies()
                    return True
                else:
                    print("⚠️ 자동 로그인 실패 - 수동 로그인 필요")
                    input("수동으로 로그인 후 Enter...")
                    self.save_cookies()
                    return True
                    
        except Exception as e:
            print(f"⚠️ 로그인 오류: {e}")
            input("수동으로 로그인 후 Enter...")
            return True
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print("✅ 쿠키 저장 완료")
        except Exception as e:
            print(f"⚠️ 쿠키 저장 실패: {e}")
    
    def load_cookies(self):
        """쿠키 로드"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                self.driver.get('https://www.naver.com')
                time.sleep(1)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
                
                self.driver.refresh()
                time.sleep(2)
                print("✅ 쿠키 로드 완료")
                return True
        except Exception as e:
            print(f"⚠️ 쿠키 로드 실패: {e}")
        return False
    
    def check_and_solve_captcha(self):
        """
        캡차 확인 및 Gemini Vision으로 자동 해결
        
        Returns:
            bool: 캡차 해결 성공 여부
        """
        try:
            time.sleep(2)
            
            # 캡차 확인
            page_source = self.driver.page_source
            is_captcha = (
                "보안 확인" in page_source or 
                "보안 학인을 완료해 주세요" in page_source or
                "구매한 물건은 총 몇 개 입니까" in page_source or
                "몇 개 입니까" in page_source
            )
            
            if not is_captcha:
                return False
            
            print("🔐 캡차 감지! Gemini로 자동 해결 시도...")
            
            # 스크린샷
            screenshot_path = 'temp_captcha.png'
            self.driver.save_screenshot(screenshot_path)
            print(f"   📸 캡차 스크린샷 저장")
            
            # Gemini Vision으로 해결
            answer = self._solve_captcha_with_gemini(screenshot_path)
            
            if answer:
                # 답 입력
                captcha_input = self.driver.find_element(By.ID, 'captchaAnswer')
                captcha_input.clear()
                captcha_input.send_keys(answer)
                time.sleep(1)
                
                # 확인 버튼
                confirm_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                confirm_btn.click()
                time.sleep(3)
                
                print(f"   ✅ 캡차 해결 완료: {answer}")
                
                # 정리
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ 캡차 처리 실패: {e}")
            return False
    
    def _solve_captcha_with_gemini(self, screenshot_path):
        """
        Gemini Vision으로 캡차 해결
        
        Args:
            screenshot_path: 스크린샷 경로
            
        Returns:
            str: 캡차 답 (숫자)
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            img = Image.open(screenshot_path)
            
            prompt = """
이 이미지는 네이버 로그인 캡차 화면입니다.
질문을 읽고 정답(숫자)만 출력하세요.

예시:
- "평수에서 구매한 물건은 총 몇 개 입니까?" → 답: 4
- "3+5=" → 답: 8

설명 없이 답(숫자)만 출력하세요:
"""
            
            response = model.generate_content([prompt, img])
            answer = response.text.strip()
            
            # 숫자만 추출
            import re
            numbers = re.findall(r'\d+', answer)
            if numbers:
                final_answer = numbers[0]
                print(f"   🤖 Gemini 답변: {final_answer}")
                return final_answer
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Gemini 캡차 해결 실패: {e}")
            return None
