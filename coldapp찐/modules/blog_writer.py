"""
블로그 작성 모듈 (원본 완전 버전)
- 블로그 글 작성
- 이미지 업로드 (단일/콜라주)
- 텍스트 스타일링
- 해시태그 추가
- 발행
"""

import time
import pyperclip
import os
import win32gui
import win32con
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class BlogWriter:
    """블로그 작성 클래스 (원본 버전)"""
    
    def __init__(self, driver):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver
        """
        self.driver = driver
    
    def write_and_publish(self, blog_id, title, ai_result, image_files, shopping_url):
        """
        블로그 글 작성 및 발행 (호환성 메서드)
        
        Args:
            blog_id: 블로그 ID
            title: 제목
            ai_result: AI 생성 결과
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
            
        Returns:
            bool: 성공 여부
        """
        self.blog_id = blog_id
        return self.write_blog_post(title, ai_result, image_files, shopping_url)
    
    def write_blog_post(self, title, ai_result, image_files, shopping_link):
        """키워드에 실제 스타일 적용 (안전한 방법)"""
        try:
            # JavaScript로 본문에서 첫 번째 키워드 찾아서 선택
            js_script = f"""
            (function() {{
                // 에디터 영역 찾기
                var editor = document.querySelector('.se-component-content');
                if (!editor) return false;
                
                // 텍스트 노드에서 키워드 찾기
                var keyword = "{keyword_text}";
                var found = false;
                
                function findAndSelect(node) {{
                    if (found) return;
                    
                    if (node.nodeType === 3) {{  // 텍스트 노드
                        var index = node.textContent.indexOf(keyword);
                        if (index >= 0) {{
                            var range = document.createRange();
                            range.setStart(node, index);
                            range.setEnd(node, index + keyword.length);
                            
                            var selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                            
                            found = true;
                            return;
                        }}
                    }} else {{
                        for (var i = 0; i < node.childNodes.length; i++) {{
                            findAndSelect(node.childNodes[i]);
                            if (found) return;
                        }}
                    }}
                }}
                
                findAndSelect(editor);
                return found;
            }})();
            """
            
            # JavaScript 실행
            result = self.driver.execute_script(js_script)
            
            if not result:
                print(f"         ⚠️ '{keyword_text}' 찾기 실패")
                return False
            
            time.sleep(0.2)
            
            # 스타일 적용
            if style_type == 'bold':
                # 굵게 버튼 클릭
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                print(f"         [굵게] '{keyword_text}'")
                
            elif style_type == 'italic':
                # 기울임 버튼 클릭
                italic_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="italic"]')
                italic_btn.click()
                print(f"         [기울임] '{keyword_text}'")
            
            elif style_type == 'underline':
                # 밑줄 버튼 클릭
                underline_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="underline"]')
                underline_btn.click()
                print(f"         [밑줄] '{keyword_text}'")
                
            elif style_type == 'font_color':
                # 글자색 버튼 클릭
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.3)
                
                # 색상 선택
                color = self._get_random_color('font')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                print(f"         [글자색{color}] '{keyword_text}'")
                
            elif style_type == 'bg_color':
                # 배경색 버튼 클릭
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.3)
                
                # 색상 선택
                color = self._get_random_color('bg')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                print(f"         [배경색{color}] '{keyword_text}'")
            
            elif style_type == 'font_size':
                # 글자 크기 버튼 클릭
                font_size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-size"]')
                font_size_btn.click()
                time.sleep(0.3)
                
                # 크기 선택 (크게 = 19pt)
                size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-value="fs19"]')
                size_btn.click()
                print(f"         [글자크기 19pt] '{keyword_text}'")
                
            elif style_type == 'bold_font':
                # 굵게 + 글자색
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
                
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.3)
                
                color = self._get_random_color('font')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                print(f"         [굵게+글자색{color}] '{keyword_text}'")
                
            elif style_type == 'bold_bg':
                # 굵게 + 배경색
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
                
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.3)
                
                color = self._get_random_color('bg')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                print(f"         [굵게+배경색{color}] '{keyword_text}'")
            
            # ✅ 수정: 스타일 적용 후 충분히 대기한 다음 해제
            time.sleep(0.5)
            self._deactivate_style(style_type)
            
            # 선택 영역 해제
            time.sleep(0.3)
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            
            return True
            
        except Exception as e:
            print(f"         [오류] 스타일 적용 실패: {e}")
            return False

    def _activate_style(self, style_type):
        """스타일 버튼 활성화 (입력 전)"""
        try:
            if style_type == 'bold':
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                btn.click()
                time.sleep(0.1)
                
            elif style_type == 'italic':
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="italic"]')
                btn.click()
                time.sleep(0.1)
                
            elif style_type == 'underline':
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="underline"]')
                btn.click()
                time.sleep(0.1)
                
            elif style_type == 'font_color':
                # 글자색 버튼 클릭
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.2)
                # 색상 선택
                color = self._get_random_color('font')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                time.sleep(0.1)
                
            elif style_type == 'bg_color':
                # 배경색 버튼 클릭
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.2)
                # 색상 선택
                color = self._get_random_color('bg')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                time.sleep(0.1)
                
            elif style_type == 'font_size':
                # 글자 크기 버튼 클릭
                font_size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-size"]')
                font_size_btn.click()
                time.sleep(0.2)
                # 크기 선택 (19pt)
                size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-value="fs19"]')
                size_btn.click()
                time.sleep(0.1)
                
            elif style_type == 'bold_font':
                # 굵게
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.1)
                # 글자색
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.2)
                color = self._get_random_color('font')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                time.sleep(0.1)
                
            elif style_type == 'bold_bg':
                # 굵게
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.1)
                # 배경색
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.2)
                color = self._get_random_color('bg')
                color_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-color="{color}"]')
                color_btn.click()
                time.sleep(0.1)
                
        except Exception as e:
            print(f"         ⚠️ 스타일 활성화 실패: {e}")
    
    def _deactivate_style(self, style_type):
        """스타일을 기본값으로 되돌리기"""
        try:
            if style_type == 'bold':
                # 굵게 OFF (토글)
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                btn.click()
                time.sleep(0.2)
                
            elif style_type == 'italic':
                # 기울임 OFF (토글)
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="italic"]')
                btn.click()
                time.sleep(0.2)
                
            elif style_type == 'underline':
                # 밑줄 OFF (토글)
                btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="underline"]')
                btn.click()
                time.sleep(0.2)
                
            elif style_type == 'font_color':
                # 글자색 → 검정색으로
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.3)
                black_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-color="#000000"]')
                black_btn.click()
                time.sleep(0.2)
                
            elif style_type == 'bg_color':
                # 배경색 → 색상 없음
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.3)
                no_color_btn = self.driver.find_element(By.CSS_SELECTOR, '.se-color-palette-no-color')
                no_color_btn.click()
                time.sleep(0.2)
                
            elif style_type == 'font_size':
                # 글자크기 → 기본 크기(16)
                font_size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-size"]')
                font_size_btn.click()
                time.sleep(0.3)
                default_size_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-value="fs16"]')
                default_size_btn.click()
                time.sleep(0.2)
                
            elif style_type == 'bold_font':
                # 굵게 OFF
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
                # 글자색 → 검정색
                font_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="font-color"]')
                font_color_btn.click()
                time.sleep(0.3)
                black_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-color="#000000"]')
                black_btn.click()
                time.sleep(0.2)
                
            elif style_type == 'bold_bg':
                # 굵게 OFF
                bold_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="bold"]')
                bold_btn.click()
                time.sleep(0.2)
                # 배경색 → 색상 없음
                bg_color_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="background-color"]')
                bg_color_btn.click()
                time.sleep(0.3)
                no_color_btn = self.driver.find_element(By.CSS_SELECTOR, '.se-color-palette-no-color')
                no_color_btn.click()
                time.sleep(0.2)
                
        except Exception as e:
            print(f"         ⚠️ 스타일 되돌리기 실패: {e}")
    
    def _insert_text_with_inline_styles(self, text, highlights, section):
        """텍스트 입력하면서 강조 부분은 바로 스타일 적용"""
        import random
        
        # 1. 이 섹션의 highlights 찾기
        section_highlights = [h for h in highlights if h.get('section') == section]
        
        if not section_highlights:
            # 강조 없으면 그냥 입력
            pyperclip.copy(text)
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            return
        
        # 2. 텍스트에서 키워드 위치 찾기
        positions = []
        for h in section_highlights:
            keyword = h.get('text', '')
            start = text.find(keyword)
            if start >= 0:
                positions.append({
                    'start': start,
                    'end': start + len(keyword),
                    'text': keyword,
                    'style': h.get('style', 'bold')
                })
        
        if not positions:
            # 이 텍스트에는 강조 없음
            pyperclip.copy(text)
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            return
        
        # 3. 위치 순서대로 정렬
        positions.sort(key=lambda x: x['start'])
        
        # 4. 섹션별 랜덤 선택 (1-3개)
        select_count = random.randint(1, min(3, len(positions)))
        selected_positions = random.sample(positions, select_count)
        selected_positions.sort(key=lambda x: x['start'])
        
        print(f"      💡 {section} 섹션: {len(positions)}개 중 {select_count}개 강조 선택")
        
        # 5. 조각별로 입력
        last_end = 0
        for pos in selected_positions:
            # 일반 텍스트 부분 입력
            if pos['start'] > last_end:
                normal_text = text[last_end:pos['start']]
                pyperclip.copy(normal_text)
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                time.sleep(0.1)
            
            # 스타일 버튼 먼저 활성화
            print(f"         [{pos['style']}] '{pos['text']}'")
            self._activate_style(pos['style'])
            
            # 강조 텍스트 입력 (스타일 적용된 상태로)
            pyperclip.copy(pos['text'])
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(0.1)
            
            # 스타일 버튼 비활성화
            self._deactivate_style(pos['style'])
            
            last_end = pos['end']
        
        # 마지막 남은 텍스트
        if last_end < len(text):
            final_text = text[last_end:]
            pyperclip.copy(final_text)
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

    def write_blog_post(self, title, ai_result, image_files, shopping_link):
        """블로그에 글 작성"""
        print(f"\n📝 블로그 글 작성 중...")
        
        try:
            # AI 결과 파싱
            ai_content = ai_result['content']
            tags = ai_result['tags']
            highlights = ai_result.get('highlights', [])  # highlights 받기
            
            print(f"   ℹ️  강조 키워드: {len(highlights)}개")
            
            # 글쓰기 페이지 이동
            self.driver.get(f'https://blog.naver.com/{self.blog_id}/postwrite')
            time.sleep(3)
            
            # 리다이렉트 (발행 버튼 노출)
            current_url = self.driver.current_url
            self.driver.get(current_url)
            time.sleep(5)
            
            # 제목 입력
            print("   ✏️  제목 입력...")
            try:
                title_div = self.driver.find_element(By.CSS_SELECTOR, "div.se-title-text")
                title_div.click()
                time.sleep(1)
                
                title_text = f"{title} 솔직 후기"
                ActionChains(self.driver).send_keys(title_text).perform()
                time.sleep(0.5)
                print(f"   ✅ 제목: {title_text}")
            except Exception as e:
                print(f"   ⚠️ 제목 입력 실패: {e}")
            
            # 본문 에디터 찾기
            print("   📄 본문 에디터 찾기...")
            editors = self.driver.find_elements(By.CSS_SELECTOR, ".se-component-content")
            if len(editors) >= 2:
                editor = editors[1]
                editor.click()
                time.sleep(1)
                print("   ✅ 본문 에디터 준비 완료")
            else:
                print("   ❌ 본문 에디터를 찾을 수 없습니다")
                return False


            
            # AI 콘텐츠 파싱 및 작성
            print("   ✍️  본문 작성 중...")
            # 이미지 순서 랜덤 섞기
            random.shuffle(image_files)
            elements = self._parse_content(ai_content, image_files, shopping_link)
            
            for idx, element in enumerate(elements):
                self._insert_element(element, highlights)  # highlights 전달
            
            print("   ✅ 본문 작성 완료!")
            
            # 링크 삽입 후 에디터 안정화 대기
            print("   ⏳ 에디터 안정화 대기 중...")
            time.sleep(2)
            
            # 해시태그를 본문 맨 끝에 추가
            print("   🏷️  해시태그 추가 시작...")
            self._insert_hashtags_in_content(tags)
            print("   ✅ 해시태그 추가 완료")
            
            # 스타일은 이미 입력하면서 적용됨
            print("   ℹ️  스타일 적용은 텍스트 입력 중 완료")
            
            # 발행하기
            print("\n🚀 발행 프로세스 시작...")
            result = self._publish_post()
            print(f"🚀 발행 프로세스 결과: {result}")
            
            return True
            
        except Exception as e:
            print(f"\n❌❌❌ 블로그 글 작성 실패! ❌❌❌")
            print(f"❌ 에러: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _parse_content(self, content, image_files, shopping_link):
        """AI 콘텐츠 파싱"""
        elements = []
        lines = content.split('\n')
        
        # 섹션 추적 변수
        current_section = 'intro'  # 시작은 도입부
        advantage_count = 0  # 장점 카운터
        is_disadvantage = False  # 단점 섹션 플래그
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # [QUOTE:VERTICAL] - 제목 인용구
            if line == '[QUOTE:VERTICAL]':
                i += 1
                if i < len(lines):
                    elements.append({
                        'type': 'quote',
                        'style': 'vertical',
                        'content': lines[i].strip(),
                        'section': 'title'
                    })
                i += 1
            
            # [QUOTE:UNDERLINE] - 장점 인용구
            elif line == '[QUOTE:UNDERLINE]':
                advantage_count += 1
                current_section = f'advantage_{advantage_count}'
                i += 1
                if i < len(lines):
                    elements.append({
                        'type': 'quote',
                        'style': 'underline',
                        'content': lines[i].strip(),
                        'section': current_section
                    })
                i += 1
            
            # [TEXT]
            elif line == '[TEXT]':
                i += 1
                if i < len(lines):
                    text_content = lines[i].strip()
                    
                    # 단점 섹션 감지 (키워드 기반)
                    disadvantage_keywords = ['아쉬운', '불편', '단점', '아쉽', '불만']
                    if any(keyword in text_content for keyword in disadvantage_keywords):
                        is_disadvantage = True
                        section = 'disadvantage'
                    elif is_disadvantage:
                        # 단점 섹션 끝나고 마무리
                        is_disadvantage = False
                        section = 'conclusion'
                        current_section = 'conclusion'
                    elif advantage_count == 0:
                        # 장점 시작 전 = 도입부
                        section = 'intro'
                    elif advantage_count > 0 and current_section.startswith('advantage'):
                        # 장점 섹션 유지
                        section = current_section
                    else:
                        section = current_section
                    
                    elements.append({
                        'type': 'text',
                        'content': text_content,
                        'section': section
                    })
                i += 1
            
            # [IMAGE:x,y] or [IMAGE:x]
            elif line.startswith('[IMAGE:'):
                nums_str = line.replace('[IMAGE:', '').replace(']', '')
                img_nums = [int(n.strip()) for n in nums_str.split(',') if n.strip().isdigit()]
                
                img_files = []
                for num in img_nums:
                    if 0 < num <= len(image_files):
                        img_files.append(image_files[num-1])
                
                if img_files:
                    elements.append({
                        'type': 'image',
                        'images': img_files,
                        'single': len(img_files) == 1,  # 단일 이미지 표시
                        'section': current_section
                    })
                i += 1
            
            # [LINK]
            elif line == '[LINK]':
                elements.append({
                    'type': 'text',
                    'content': shopping_link,
                    'section': 'conclusion'
                })
                i += 1
            
            else:
                i += 1
        
        return elements
    
    def _insert_element(self, element, highlights=None):
        """요소 삽입"""
        elem_type = element['type']
        
        try:
            # 인용구
            if elem_type == 'quote':
                # 인용구 스타일 랜덤 선택 (실제 존재하는 스타일만)
                import random
                quote_styles = [
                    'quotation_line',       # 세로 라인
                    'quotation_underline',  # 밑줄
                    'quotation_corner'      # 코너
                ]
                target_value = random.choice(quote_styles)
                print(f"      🎨 인용구 스타일: {target_value}")
                
                # 옵션 버튼 클릭
                option_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-name="insert-quotation"] .se-document-toolbar-select-option-button')
                option_btn.click()
                time.sleep(1)
                
                # 스타일 선택
                quote_btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-value="{target_value}"]')
                quote_btn.click()
                time.sleep(0.5)
                
                # 텍스트 입력
                pyperclip.copy(element['content'])
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                time.sleep(0.5)
                
                # 인용구 빠져나오기
                ActionChains(self.driver).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(0.2)
                ActionChains(self.driver).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(0.5)
            
            # 텍스트
            elif elem_type == 'text':
                content = element['content']
                section = element.get('section', 'unknown')  # 섹션 정보
                
                # 마크다운 제거
                content = self._remove_markdown(content)
                
                # 문장 단위로 나누기 (마침표, 느낌표, 물음표 기준)
                sentences = re.split(r'([.!?]\s+)', content)
                all_sentences = []
                
                for i in range(0, len(sentences)-1, 2):
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    if sentence.strip():
                        all_sentences.append(sentence.strip())
                
                # 마지막 문장 처리
                if len(sentences) % 2 == 1 and sentences[-1].strip():
                    all_sentences.append(sentences[-1].strip())
                
                # 2-3문장씩 묶어서 문단 구성
                formatted_text = ""
                i = 0
                while i < len(all_sentences):
                    # 2-3문장을 하나의 문단으로
                    paragraph_size = 2 if (i + 2) % 5 == 0 else 3  # 2문장, 3문장 번갈아가며
                    paragraph = " ".join(all_sentences[i:i+paragraph_size])
                    formatted_text += paragraph + "\n\n"
                    i += paragraph_size
                
                # highlights가 있으면 스타일 적용하면서 입력, 없으면 그냥 입력
                if highlights:
                    self._insert_text_with_inline_styles(formatted_text.strip(), highlights, section)
                else:
                    pyperclip.copy(formatted_text.strip())
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                
                time.sleep(0.5)
                ActionChains(self.driver).send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform()
                time.sleep(0.5)
            
            # 이미지
            elif elem_type == 'image':
                if element.get('single', False):
                    # 단일 이미지: 콜라주 없이
                    self._upload_single_image(element['images'][0])
                else:
                    # 여러 이미지: 콜라주
                    self._upload_collage_images(element['images'])
                
        except Exception as e:
            print(f"      ⚠️ 요소 삽입 실패: {e}")
    
    def _insert_hashtags_in_content(self, tags):
        """본문 끝에 해시태그 추가"""
        print("   🏷️  해시태그 추가 중...")
        
        try:
            # 해시태그 텍스트 생성
            hashtag_text = " ".join([f"#{tag}" for tag in tags])
            
            # 클립보드에 복사
            pyperclip.copy(hashtag_text)
            
            # 붙여넣기
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(0.5)
            
            print(f"   ✅ 해시태그 {len(tags)}개 추가 완료!")
            print(f"      예시: {' '.join([f'#{tag}' for tag in tags[:3]])}...")
            
        except Exception as e:
            print(f"   ⚠️ 해시태그 추가 실패: {e}")
    
    def _publish_post(self):
        """블로그 글 발행"""
        print("\n" + "="*60)
        print("📤 블로그 글 발행 시작!")
        print("="*60)
        
        try:
            # 해시태그 입력 후 대기
            print("   ⏳ 발행 전 대기 중...")
            time.sleep(2)
            
            # 발행 버튼 찾기 (오른쪽 상단)
            print("   🔍 발행 버튼 찾는 중...")
            publish_selectors = [
                "button[data-testid='publish-btn']",
                "button.publish_btn",
                "button.se-publish-button",
                "button[aria-label='발행']",
                "button"  # 모든 버튼
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"      셀렉터 '{selector}': {len(buttons)}개 버튼 발견")
                    for btn in buttons:
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.strip()
                                if '발행' in btn_text:
                                    publish_btn = btn
                                    print(f"      ✅ 발행 버튼 찾음: '{btn_text}'")
                                    break
                        except:
                            continue
                    if publish_btn:
                        break
                except Exception as e:
                    print(f"      셀렉터 '{selector}' 실패: {e}")
                    continue
            
            if not publish_btn:
                print("   ❌ 발행 버튼을 찾을 수 없습니다!")
                print("   ℹ️  현재 URL:", self.driver.current_url)
                print("   ℹ️  수동으로 발행해주세요.")
                return False
            
            # 첫 번째 발행 버튼 클릭
            publish_btn.click()
            time.sleep(2)
            print("   ✅ 발행 버튼 클릭")
            
            # 발행 확인 버튼 클릭 (팝업)
            print("   🔍 발행 확인 버튼 찾는 중...")
            confirm_btn = None
            
            confirm_selectors = [
                "button[data-testid='seOnePublishBtn']",
                "button.confirm_btn__WEaBq",
                "button.se-publish-confirm"
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if confirm_btn and confirm_btn.is_displayed():
                        print(f"      ✅ 확인 버튼 찾음: {selector}")
                        break
                    else:
                        confirm_btn = None
                except:
                    continue
            
            if confirm_btn:
                confirm_btn.click()
                time.sleep(3)
                print("   ✅ 발행 확인 완료!")
                print("\n" + "="*60)
                print("🎉 블로그 글 발행 성공!")
                print("="*60)
                return True
            else:
                print("   ❌ 발행 확인 버튼을 찾을 수 없습니다!")
                print("   ℹ️  팝업이 안 열렸을 수 있습니다.")
                return False
                
        except Exception as e:
            print(f"   ⚠️ 발행 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _upload_single_image(self, image_file):
        """단일 이미지 업로드 (콜라주 없이)"""
        try:
            # 사진 버튼 클릭
            photo_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='image']")
            photo_btn.click()
            time.sleep(3)
            
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
            
            if not file_input:
                return
            
            # 파일 업로드 (단일)
            file_input.send_keys(image_file)
            time.sleep(1)
            
            # 파일 선택 창 닫기 (win32gui 직접 종료)
            def find_window_by_title(title_part):
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title_part in window_title:
                            windows.append(hwnd)
                    return True
                
                windows = []
                win32gui.EnumWindows(callback, windows)
                return windows[0] if windows else None
            
            hwnd = None
            for i in range(5):
                time.sleep(1)
                hwnd = find_window_by_title("열기")
                if hwnd:
                    break
            
            if hwnd:
                # WM_CLOSE 메시지로 창 닫기
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                time.sleep(2)
            
            print(f"      ✅ 단일 이미지 업로드 완료")
            
        except Exception as e:
            print(f"      ⚠️ 단일 이미지 업로드 실패: {e}")
    
    def _upload_collage_images(self, image_files):
        """콜라주 이미지 업로드"""
        try:
            # 사진 버튼 클릭
            photo_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-name='image']")
            photo_btn.click()
            time.sleep(3)
            
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
            
            if not file_input:
                return
            
            # 파일 업로드
            files_path = '\n'.join(image_files)
            file_input.send_keys(files_path)
            time.sleep(1)
            
            # 파일 선택 창 닫기 (win32gui 직접 종료)
            def find_window_by_title(title_part):
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if title_part in window_title:
                            windows.append(hwnd)
                    return True
                
                windows = []
                win32gui.EnumWindows(callback, windows)
                return windows[0] if windows else None
            
            hwnd = None
            for i in range(5):
                time.sleep(1)
                hwnd = find_window_by_title("열기")
                if hwnd:
                    break
            
            if hwnd:
                # WM_CLOSE 메시지로 창 닫기
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                time.sleep(2)
            
            # 콜라주 버튼 클릭
            if len(image_files) >= 2:
                time.sleep(2)
                collage_label = self.driver.find_element(By.CSS_SELECTOR, "label[for='image-type-collage']")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", collage_label)
                time.sleep(0.5)
                collage_label.click()
                time.sleep(2)
                
        except Exception as e:
            print(f"      ⚠️ 이미지 업로드 실패: {e}")
    
    def _get_random_color(self, color_type='font'):
        """랜덤 색상 선택 (네이버 에디터 실제 색상)"""
        if color_type == 'font':
            # 글자색: 진한 색상 위주
            font_colors = [
                '#ff5f45', '#ffa94f', '#ffef34', '#98d36c', '#00b976', '#00bfb5',
                '#00cdff', '#0095e9', '#bc61ab', '#ff65a8', '#ff0010', '#ff9300',
                '#ffd300', '#54b800', '#00a84b', '#009d91', '#00b3f2', '#0078cb',
                '#aa1f91', '#ff008c', '#ba0000', '#b85c00', '#ac9a00', '#36851e',
                '#007433', '#00756a', '#007aa6', '#004e82', '#740060', '#bb005c',
                '#700001', '#823f00', '#6a5f00', '#245b12', '#004e22', '#00554c',
                '#004e6a', '#003960', '#4f0041', '#830041', '#333333', '#555555',
                '#777777', '#999999'
            ]
            return random.choice(font_colors)
        else:
            # 배경색: 연한 색상 위주 (형광펜 효과)
            bg_colors = [
                '#ffcdc0', '#ffe3c8', '#fff8b2', '#e3fdc8', '#c2f4db', '#bdfbfa',
                '#b0f1ff', '#9bdfff', '#fdd5f5', '#ffb7de', '#ffad98', '#ffd1a4',
                '#fff593', '#badf98', '#3fcc9c', '#15d0ca', '#28e1ff', '#5bc7ff',
                '#cd8bc0', '#ff97c1', '#f7f7f7', '#e2e2e2', '#c2c2c2', '#ffffff'
            ]
            return random.choice(bg_colors)
    
    def _remove_markdown(self, text):
        """마크다운 기호 제거"""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        return text
    
    def close(self):
        """브라우저 종료 (여기서는 사용 안 함, 메인 클래스에서 처리)"""
        pass
