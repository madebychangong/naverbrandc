"""
블로그 작성 모듈
- 블로그 글 작성
- 이미지 업로드
- 태그 추가
- 발행
"""

import time
import pyperclip
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class BlogWriter:
    """블로그 작성 클래스"""
    
    def __init__(self, driver):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver
        """
        self.driver = driver
    
    def write_and_publish(self, blog_id, title, ai_result, image_files, shopping_url):
        """
        블로그 글 작성 및 발행
        
        Args:
            blog_id: 블로그 ID
            title: 제목
            ai_result: AI 생성 결과 {'content': ..., 'tags': ..., 'highlights': ...}
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
            
        Returns:
            bool: 성공 여부
        """
        print(f"\n📝 블로그 글 작성 중...")
        
        try:
            # 블로그 쓰기 페이지 이동
            write_url = f"https://blog.naver.com/{blog_id}/postwrite"
            self.driver.get(write_url)
            time.sleep(5)
            
            # 제목 입력
            print("   ✍️  제목 입력...")
            title_input = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="제목을 입력하세요"]')
            title_input.click()
            time.sleep(0.5)
            pyperclip.copy(title)
            title_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            
            # 본문 에디터로 이동
            print("   ✍️  본문 작성...")
            editor = self.driver.find_element(By.CSS_SELECTOR, '.se-component-content')
            editor.click()
            time.sleep(1)
            
            # 본문 작성 (간소화 버전 - 태그 파싱 없이 그냥 입력)
            content = ai_result['content']
            
            # [TEXT], [IMAGE:1], [LINK] 등 태그를 간단히 처리
            self._write_content_simple(content, image_files, shopping_url)
            
            # 태그 추가
            if ai_result.get('tags'):
                print(f"   🏷️  태그 추가 ({len(ai_result['tags'])}개)...")
                self._add_tags(ai_result['tags'])
            
            print("   ✅ 블로그 글 작성 완료!")
            print("   ℹ️  수동으로 발행 버튼을 눌러주세요.")
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ 블로그 작성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _write_content_simple(self, content, image_files, shopping_url):
        """
        본문 작성 (간소화 버전)
        태그를 간단히 처리해서 텍스트와 이미지를 삽입
        
        Args:
            content: AI 생성 본문 (태그 포함)
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
        """
        import re
        
        # 라인별로 처리
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # [TEXT] 태그 처리
            if line.startswith('[TEXT]'):
                continue
            
            # [QUOTE:VERTICAL] 또는 [QUOTE:UNDERLINE] 처리
            if line.startswith('[QUOTE:'):
                # 인용구로 표시 (굵게)
                quote_text = re.sub(r'\[QUOTE:.*?\]', '', line).strip()
                if quote_text:
                    self._insert_text(quote_text, bold=True)
                    self._press_enter(2)
                continue
            
            # [IMAGE:x] 또는 [IMAGE:x,y] 처리
            if line.startswith('[IMAGE:'):
                image_nums = re.findall(r'\d+', line)
                image_indices = [int(n) - 1 for n in image_nums]  # 1-based → 0-based
                
                images_to_upload = []
                for idx in image_indices:
                    if 0 <= idx < len(image_files):
                        images_to_upload.append(image_files[idx])
                
                if images_to_upload:
                    self._upload_images(images_to_upload)
                    self._press_enter(2)
                continue
            
            # [LINK] 태그 처리
            if line.startswith('[LINK]'):
                self._insert_link(shopping_url)
                self._press_enter(2)
                continue
            
            # 일반 텍스트
            if line and not line.startswith('['):
                self._insert_text(line)
                self._press_enter()
    
    def _insert_text(self, text, bold=False):
        """텍스트 삽입"""
        if bold:
            # 굵게 버튼 클릭
            try:
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
            except:
                pass
        
        pyperclip.copy(text)
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(0.3)
        
        if bold:
            # 굵게 해제
            try:
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
            except:
                pass
    
    def _press_enter(self, count=1):
        """엔터 입력"""
        for _ in range(count):
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(0.2)
    
    def _upload_images(self, image_paths):
        """이미지 업로드 (단순 버전)"""
        try:
            # 사진 버튼 클릭
            photo_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='image']")
            photo_btn.click()
            time.sleep(2)
            
            # file input 찾기
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            file_input = None
            for inp in file_inputs:
                try:
                    accept = inp.get_attribute('accept')
                    if accept and 'image' in accept:
                        file_input = inp
                        break
                except:
                    pass
            
            if not file_input and file_inputs:
                file_input = file_inputs[0]
            
            if file_input:
                # 파일 업로드
                files_path = '\n'.join(image_paths)
                file_input.send_keys(files_path)
                time.sleep(3)
                
                print(f"      ✅ {len(image_paths)}개 이미지 업로드 완료")
            
        except Exception as e:
            print(f"      ⚠️ 이미지 업로드 실패: {e}")
    
    def _insert_link(self, url):
        """링크 삽입"""
        try:
            # 링크 버튼 클릭
            link_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='link']")
            link_btn.click()
            time.sleep(1)
            
            # URL 입력
            url_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='URL을 입력하세요']")
            url_input.clear()
            pyperclip.copy(url)
            url_input.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.5)
            
            # 확인 버튼
            confirm_btn = self.driver.find_element(By.CSS_SELECTOR, "button.se-popup-button-confirm")
            confirm_btn.click()
            time.sleep(1)
            
            print(f"      ✅ 링크 삽입 완료")
            
        except Exception as e:
            print(f"      ⚠️ 링크 삽입 실패: {e}")
    
    def _add_tags(self, tags):
        """태그 추가"""
        try:
            # 태그 입력창 클릭
            tag_input = self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="태그 입력"]')
            tag_input.click()
            time.sleep(0.5)
            
            for tag in tags[:10]:  # 최대 10개
                pyperclip.copy(tag)
                tag_input.send_keys(Keys.CONTROL, 'v')
                time.sleep(0.3)
                tag_input.send_keys(Keys.ENTER)
                time.sleep(0.3)
            
            print(f"      ✅ {len(tags[:10])}개 태그 추가 완료")
            
        except Exception as e:
            print(f"      ⚠️ 태그 추가 실패: {e}")
