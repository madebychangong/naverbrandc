"""
네이버 블로그 자동화 프로그램
- 쇼핑 URL 입력 → 제품 정보 추출 → AI 글 생성 → 블로그 발행
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyperclip
import os
import win32gui
import win32con
import requests
import re
import random


class NaverBlogAutomation:
    """네이버 블로그 자동화 클래스"""
    
    def __init__(self, blog_id, naver_id, naver_pw, gemini_api_key, chrome_profile_name='default'):
        self.blog_id = blog_id
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.gemini_api_key = gemini_api_key
        self.chrome_profile_name = chrome_profile_name
        self.driver = None

        # temp_images 폴더도 프로세스 ID로 분리 (다중 프로그램 실행 시 충돌 방지)
        process_id = os.getpid()
        self.temp_images_dir = os.path.join(os.getcwd(), f'temp_images_{process_id}')

        # 쿠키 파일 경로 (AppData에 숨김 저장) - 프로필별로 분리
        config_dir = os.path.join(os.getenv('APPDATA'), 'ColdAPP')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        self.cookies_file = os.path.join(config_dir, f'naver_cookies_{chrome_profile_name}.json')

        # temp_images 폴더 생성
        if not os.path.exists(self.temp_images_dir):
            os.makedirs(self.temp_images_dir)

    def _soft_avoid_phrases(self, text: str) -> str:
        """상투 문구의 빈도를 낮추기 위한 후처리: 동일 그룹 표현은 최대 1회 유지하고 나머지는 동의어로 치환.
        태그([TEXT] 등)는 보존.
        """
        groups = [
            {
                'targets': [
                    '안녕하세요!', '안녕하세요.', '안녕하세요',
                    '요즘 필요한 제품을 찾다가', '여러 제품을 비교해본 결과'
                ],
                'alts': ['첫 느낌부터', '처음 보고 느낀 건', '필요가 생겨 제품을 찾아보던 중', '사용 배경부터']
            },
            {
                'targets': ['정말 만족스러웠어요', '만족스러웠어요', '정말 만족스럽습니다'],
                'alts': ['쓸 만했습니다', '기대치엔 부합했습니다', '체감 성능은 무난했습니다']
            },
            {
                'targets': ['가성비가 좋아요', '가격 대비 이 정도면 충분해요', '가격 대비 괜찮아요'],
                'alts': ['가격 대비 포지션은 명확합니다', '동급 대비 조건은 나쁘지 않습니다', '예산 대비 선택지는 됩니다']
            },
            {
                'targets': ['추천드립니다', '추천합니다', '강추합니다'],
                'alts': ['선택지로 고려해볼 만합니다', '이런 용도라면 맞을 수 있습니다', '상황에 따라 유효한 대안이 됩니다']
            },
            {
                'targets': ['물론 완벽한 제품은 없듯이', '아쉬운 부분도 있었어요'],
                'alts': ['완벽하진 않아서', '쓰다 보니 보완할 지점도 있습니다']
            }
        ]
        for group in groups:
            pattern = re.compile('|'.join(re.escape(t) for t in group['targets']))
            cnt = {'n': 0}
            def repl(m):
                cnt['n'] += 1
                if cnt['n'] == 1:
                    # 첫 등장은 50% 확률로 유지, 아니면 치환
                    return m.group(0) if random.random() < 0.5 else random.choice(group['alts'])
                return random.choice(group['alts'])
            text = pattern.sub(repl, text)
        return text

    def _remove_markdown(self, text):
        """마크다운 기호 제거"""
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        return text
    
    def _get_random_color(self, color_type='font'):
        """랜덤 색상 선택 (네이버 에디터에 실제로 있는 색상)"""
        import random
        
        # 네이버 에디터 실제 색상 팔레트 (글자색/배경색 공통)
        all_colors = [
            '#999999', '#ffcdc0', '#ffe3c8', '#fff8b2', '#e3fdc8', '#c2f4db', 
            '#bdfbfa', '#b0f1ff', '#9bdfff', '#fdd5f5', '#ffb7de', '#ffffff',
            '#777777', '#ffad98', '#ffd1a4', '#fff593', '#badf98', '#3fcc9c',
            '#15d0ca', '#28e1ff', '#5bc7ff', '#cd8bc0', '#ff97c1', '#f7f7f7',
            '#555555', '#ff5f45', '#ffa94f', '#ffef34', '#98d36c', '#00b976',
            '#00bfb5', '#00cdff', '#0095e9', '#bc61ab', '#ff65a8', '#e2e2e2',
            '#333333', '#ff0010', '#ff9300', '#ffd300', '#54b800', '#00a84b',
            '#009d91', '#00b3f2', '#0078cb', '#aa1f91', '#ff008c', '#c2c2c2',
            '#141414', '#ba0000', '#b85c00', '#ac9a00', '#36851e', '#007433',
            '#00756a', '#007aa6', '#004e82', '#740060', '#bb005c', '#9c9c9c',
            '#000000', '#700001', '#823f00', '#6a5f00', '#245b12', '#004e22',
            '#00554c', '#004e6a', '#003960', '#4f0041', '#830041'
        ]
        
        if color_type == 'font':
            # 글자색: 진한 색상 위주 선택
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
            # 배경색: 연한 색상 위주 선택 (형광펜 효과)
            bg_colors = [
                '#ffcdc0', '#ffe3c8', '#fff8b2', '#e3fdc8', '#c2f4db', '#bdfbfa',
                '#b0f1ff', '#9bdfff', '#fdd5f5', '#ffb7de', '#ffad98', '#ffd1a4',
                '#fff593', '#badf98', '#3fcc9c', '#15d0ca', '#28e1ff', '#5bc7ff',
                '#cd8bc0', '#ff97c1', '#f7f7f7', '#e2e2e2', '#c2c2c2', '#ffffff'
            ]
            return random.choice(bg_colors)
    
    def _apply_text_style_to_keyword(self, keyword_text, style_type):
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

    def start_browser(self):
        """브라우저 시작 (다중 프로세스 지원 - 완전한 프로필 격리)"""
        print("🌐 Chrome 브라우저 시작...")

        # 설정에서 지정한 프로필 이름 사용 (프로그램마다 다른 이름 지정 필수)
        import os
        import random

        # 프로젝트 폴더 내에 chrome_profiles 폴더 생성
        profiles_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chrome_profiles')
        if not os.path.exists(profiles_base):
            os.makedirs(profiles_base)

        # 설정된 프로필 이름으로 완전히 독립적인 사용자 데이터 디렉토리
        user_data_dir = os.path.join(profiles_base, self.chrome_profile_name)

        print(f"   📁 프로필 이름: {self.chrome_profile_name}")
        print(f"   📁 프로필 경로: {user_data_dir}")

        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        options.add_argument(f'--user-data-dir={user_data_dir}')

        # Chrome 프로필 완전 격리 설정
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-sync')  # Chrome 동기화 비활성화
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins-discovery')

        # 각 프로세스마다 독립적인 프로필 디렉토리 사용
        options.add_argument(f'--profile-directory=Default')

        # 포트 충돌 방지를 위해 랜덤 포트 사용
        driver_port = random.randint(9000, 9999)

        self.driver = uc.Chrome(
            options=options,
            version_main=141,
            driver_executable_path=None,
            port=driver_port
        )
        print(f"✅ 브라우저 시작 완료 (프로필: {self.chrome_profile_name}, Port: {driver_port})")
    
    def save_cookies(self):
        """쿠키 저장"""
        try:
            import json
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print("✅ 쿠키 저장 완료")
        except Exception as e:
            print(f"⚠️ 쿠키 저장 실패: {e}")
    
    def load_cookies(self):
        """쿠키 로드"""
        try:
            import json
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
    
    def login(self):
        """네이버 로그인"""
        print("\n🔐 네이버 로그인...")
        
        # 쿠키로 로그인 시도
        if self.load_cookies():
            # 로그인 확인
            self.driver.get('https://www.naver.com')
            time.sleep(2)
            
            if 'blog.naver.com' in self.driver.current_url or 'NID_AUT' in self.driver.page_source:
                print("✅ 쿠키 로그인 성공!")
                return True
            else:
                print("⚠️ 쿠키 만료, 재로그인 필요")
        
        # 네이버 메인
        self.driver.get('https://www.naver.com')
        time.sleep(2)
        
        # 로그인 페이지
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
                self.save_cookies()  # 쿠키 저장
                return True
            else:
                # 캡차 확인
                if self._check_and_solve_captcha():
                    print("✅ 캡차 해결 후 로그인 성공!")
                    self.save_cookies()  # 쿠키 저장
                    return True
                else:
                    print("⚠️ 자동 로그인 실패 - 수동 로그인 필요")
                    input("수동으로 로그인 후 Enter...")
                    self.save_cookies()  # 쿠키 저장
                    return True
                
        except Exception as e:
            print(f"⚠️ 로그인 오류: {e}")
            input("수동으로 로그인 후 Enter...")
            return True
    
    def _check_and_solve_captcha(self):
        """캡차 확인 및 자동 해결"""
        try:
            time.sleep(2)  # 페이지 로드 대기
            
            # 캡차 확인 (여러 방법으로)
            page_source = self.driver.page_source
            is_captcha = (
                "보안 확인" in page_source or 
                "보안 학인을 완료해 주세요" in page_source or
                "구매한 물건은 총 몇 개 입니까" in page_source or
                "몇 개 입니까" in page_source
            )
            
            if is_captcha:
                print("🔐 캡차 감지! Gemini로 자동 해결 시도...")
                
                # 전체 화면 스크린샷
                screenshot_path = os.path.join(self.temp_images_dir, 'captcha.png')
                self.driver.save_screenshot(screenshot_path)
                print(f"   📸 캡차 스크린샷 저장: {screenshot_path}")
                
                # Gemini Vision으로 캡차 해결
                answer = self._solve_captcha_with_gemini(screenshot_path)
                
                if answer:
                    # 답 입력
                    try:
                        # 입력창 찾기 (여러 셀렉터 시도)
                        answer_input = None
                        selectors = [
                            "input[type='text']",
                            "input[type='number']",
                            "input.input",
                            "input[placeholder*='입력']",
                            "input"
                        ]
                        
                        for selector in selectors:
                            try:
                                inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for inp in inputs:
                                    if inp.is_displayed():
                                        answer_input = inp
                                        break
                                if answer_input:
                                    break
                            except:
                                continue
                        
                        if answer_input:
                            answer_input.clear()
                            answer_input.send_keys(answer)
                            time.sleep(1)
                            print(f"   ✅ 답변 입력: {answer}")
                            
                            # 확인 버튼 클릭
                            submit_selectors = [
                                "button[type='submit']",
                                "button.btn",
                                "button",
                                "input[type='submit']"
                            ]
                            
                            for selector in submit_selectors:
                                try:
                                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    for btn in buttons:
                                        if btn.is_displayed() and ("확인" in btn.text or "로딩" in btn.text or btn.get_attribute("type") == "submit"):
                                            btn.click()
                                            print(f"   ✅ 확인 버튼 클릭")
                                            time.sleep(5)
                                            return True
                                except:
                                    continue
                            
                            # Enter로 제출
                            answer_input.send_keys(Keys.ENTER)
                            time.sleep(5)
                            print(f"   ✅ Enter로 제출")
                            return True
                        else:
                            print(f"   ⚠️ 입력창을 찾을 수 없습니다")
                            
                    except Exception as e:
                        print(f"   ⚠️ 캡차 답변 입력 실패: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"   ⚠️ Gemini가 답을 찾지 못했습니다")
                
                return False
            
            return False
            
        except Exception as e:
            print(f"⚠️ 캡차 처리 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _solve_captcha_with_gemini(self, image_path):
        """Gemini Vision으로 캡차 해결"""
        try:
            import google.generativeai as genai
            from PIL import Image
            
            genai.configure(api_key=self.gemini_api_key)
            
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("   🤖 모델: gemini-2.5-pro")
            except:
                model = genai.GenerativeModel('gemini-2.5-flash')
                print("   🤖 모델: gemini-2.5-flash (백업)")
            
            # 이미지 로드
            img = Image.open(image_path)
            
            # Gemini에게 캡차 해결 요청
            prompt = """
이 이미지는 네이버 보안 인증 화면입니다.
이미지 속 수학 문제를 찾아서 답만 숫자로 출력하세요.

예시:
- "평수에서 구입한 물건은 총 몇 개 입니까?" → 답: 4
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
    
    def extract_product_info(self, shopping_url):
        """쇼핑 URL에서 제품 정보 추출"""
        print(f"\n📦 제품 정보 추출 중...")
        print(f"   URL: {shopping_url}")
        
        try:
            # URL 접근 (naver.me 짧은 URL도 리다이렉트 후 그대로 사용)
            if 'naver.me' in shopping_url:
                print("   🔄 짧은 URL 리다이렉트 확인...")
                self.driver.get(shopping_url)
                time.sleep(3)
                final_url = self.driver.current_url
                print(f"   ✅ 리다이렉트: {final_url}")
                
                # 캡차 확인 및 해결
                if self._check_and_solve_captcha():
                    print("   ✅ 캡차 해결 완료")
                    time.sleep(3)
                
                print(f"   ✅ 페이지 로드 완료")
                time.sleep(3)
            else:
                # 일반 URL (smartstore, brand 등)
                print(f"   🔄 URL 접근 중...")
                self.driver.get(shopping_url)
                time.sleep(5)
                
                # 캡차 확인 및 해결
                if self._check_and_solve_captcha():
                    print("   ✅ 캡차 해결 완료")
                    time.sleep(3)
                
                print(f"   ✅ 페이지 로드 완료")
            
            # 제품 정보 추출
            title = self._extract_title()
            price = self._extract_price()
            description = self._extract_description()
            images = self._extract_images()
            
            print(f"\n✅ 제품 정보 추출 완료:")
            print(f"   - 제품명: {title[:50]}...")
            print(f"   - 가격: {price}")
            print(f"   - 설명: {len(description)}자")
            print(f"   - 이미지: {len(images)}개")
            
            return {
                'title': title,
                'price': price,
                'description': description,
                'images': images,
                'link': shopping_url
            }
            
        except Exception as e:
            print(f"❌ 제품 정보 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_title(self):
        """제품명 추출"""
        selectors = [
            'h3.YbkZ4Jg2_z',    # 초기 버전
            'h3.DCVBehA8ZB',    # 변경 후 버전
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    title = element.text.strip()
                    if title and len(title) > 3:
                        # [히든딜], [커넥트 히든딜] 등 대괄호 패턴 제거
                        title = re.sub(r'^\[.*?\]\s*', '', title)
                        return title
            except:
                continue
        
        return "제품명을 찾을 수 없습니다"
    
    def _extract_price(self):
        """가격 추출"""
        selectors = [
            'span.xMK43',
            'span._1LY7DqCnwR',
            '.price',
            '[class*="price"]'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    price = element.text.strip()
                    if price and ('원' in price or ',' in price):
                        return price
            except:
                continue
        
        return "가격 정보 없음"
    
    def _extract_description(self):
        """제품 설명 추출"""
        exclude_keywords = ['상품정보 제공고시', '배송', '반품', '교환', '문의', '결제', '주문']
        
        selectors = [
            'div.se-main-container',   # 상세정보 메인 영역
            'div.se-viewer',            # 백업
            'div.nKuwJ',
            'div._3cWR_0Clkt',
        ]
        
        description_parts = []
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 10:
                        # 제외 키워드 필터링
                        if not any(keyword in text for keyword in exclude_keywords):
                            description_parts.append(text)
                            if len(' '.join(description_parts)) > 500:
                                break
            except:
                continue
            
            if len(' '.join(description_parts)) > 500:
                break
        
        if description_parts:
            return ' '.join(description_parts)[:500]
        
        return "제품 설명을 찾을 수 없습니다"
    
    def _extract_images(self):
        """이미지 URL 추출 (썸네일 클릭 방식 + 메인 이미지 대체)"""
        print("   📸 이미지 수집 중...")
        image_urls = []
        
        try:
            # 썸네일 리스트 찾기
            thumbnail_selector = 'li.AIvsO_QzbN a'
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, thumbnail_selector)
            
            print(f"   🔍 썸네일 {len(thumbnails)}개 발견")
            
            if len(thumbnails) > 0:
                # 썸네일이 있으면 클릭 방식
                for idx, thumbnail in enumerate(thumbnails[:6]):  # 최대 6개
                    try:
                        # 썸네일 클릭
                        thumbnail.click()
                        time.sleep(0.8)  # 로딩 시간 증가
                        
                        # 메인 이미지 가져오기 (여러 셀렉터 시도)
                        main_img = None
                        selectors = [
                            'img.TgO1N1wWTm[alt="대표이미지"]',
                            'img.TgO1N1wWTm',
                            'div._2LuLme7XCi img',
                            'div.image_viewer img',
                            'img[alt="대표이미지"]',
                            'img[class*="image"]',
                        ]
                        
                        for selector in selectors:
                            try:
                                main_img = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if main_img and main_img.get_attribute('src'):
                                    break
                            except:
                                continue
                        
                        if not main_img:
                            print(f"      ⚠️ 이미지 {idx+1}: 메인 이미지 요소를 찾을 수 없음")
                            continue
                        
                        src = main_img.get_attribute('src')
                        
                        if not src:
                            print(f"      ⚠️ 이미지 {idx+1}: src 속성 없음")
                            continue
                        
                        # 고화질 이미지로 변환
                        if '?type=' in src:
                            src = src.split('?type=')[0] + '?type=f640'
                        
                        if src and src not in image_urls:
                            image_urls.append(src)
                            print(f"      ✅ 이미지 {len(image_urls)}: {src[:60]}...")
                            
                            if len(image_urls) >= 6:
                                break
                                
                    except Exception as e:
                        print(f"      ⚠️ 이미지 {idx+1} 추출 실패: {e}")
                        continue
            else:
                # 썸네일이 없으면 메인 이미지 직접 가져오기
                print("   ℹ️  썸네일 없음 - 메인 이미지 직접 추출")
                
                # 여러 셀렉터 시도
                selectors = [
                    'img.TgO1N1wWTm[alt="대표이미지"]',
                    'img.TgO1N1wWTm',
                    'div._2LuLme7XCi img',
                    'div.image_viewer img',
                    'img[alt="대표이미지"]',
                    'div._2X4tyqLO8t img',  # 추가 셀렉터
                    'img[class*="TgO"]',  # 클래스 일부 매칭
                ]
                
                for selector in selectors:
                    try:
                        print(f"      🔍 시도 중: {selector}")
                        main_img = self.driver.find_element(By.CSS_SELECTOR, selector)
                        src = main_img.get_attribute('src')
                        
                        if not src:
                            continue
                        
                        # 고화질 이미지로 변환
                        if '?type=' in src:
                            src = src.split('?type=')[0] + '?type=f640'
                        
                        if src:
                            image_urls.append(src)
                            print(f"      ✅ 메인 이미지: {src[:60]}...")
                            break
                    except Exception as e:
                        print(f"      ⚠️ {selector} 실패: {e}")
                        continue
            
            print(f"   ✅ 총 {len(image_urls)}개 이미지 추출 완료")
            return image_urls
            
        except Exception as e:
            print(f"   ⚠️ 이미지 추출 오류: {e}")
            return []
    
    def download_images(self, image_urls):
        """이미지 다운로드"""
        print(f"\n💾 이미지 다운로드 중...")
        print(f"   📊 다운로드할 이미지: {len(image_urls)}개")
        
        if not image_urls:
            print("   ⚠️ 이미지 URL이 없습니다!")
            return []
        
        downloaded_files = []
        
        for idx, url in enumerate(image_urls):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    filename = f"product_{idx+1}.jpg"
                    filepath = os.path.join(self.temp_images_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    abs_path = os.path.abspath(filepath)
                    downloaded_files.append(abs_path)
                    print(f"   ✅ {filename} 다운로드 완료")
                    
            except Exception as e:
                print(f"   ⚠️ 이미지 {idx+1} 다운로드 실패: {e}")
                continue
        
        print(f"✅ {len(downloaded_files)}개 이미지 다운로드 완료")
        return downloaded_files
    
    def generate_ai_content(self, product_info, image_files=None):
        """Gemini AI로 블로그 글 생성 (Vision API 사용 + 히스토리 학습)"""
        print(f"\n🤖 AI 글 생성 중...")

        try:
            import google.generativeai as genai
            from modules.content_history import ContentHistoryManager

            genai.configure(api_key=self.gemini_api_key)

            # 모델 우선순위: gemini-2.5-flash → Gemini 2.5 Flash-Lite
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("   🤖 모델: gemini-2.5-pro")
            except:
                model = genai.GenerativeModel('gemini-2.5-flash')
                print("   🤖 모델: gemini-2.5-flash (백업)")

            title = product_info['title']
            price = product_info['price']
            description = product_info['description']
            image_count = len(product_info['images'])

            # 히스토리 관리자 초기화 및 차별화 전략 가져오기
            history_manager = ContentHistoryManager()
            differentiation = history_manager.suggest_differentiation_strategy(title)

            print(f"   📚 카테고리: {differentiation['category']}")
            if differentiation['recent_count'] > 0:
                print(f"   📊 최근 {differentiation['recent_count']}개 리뷰 분석 완료")
                print(f"   💡 추천 각도: {', '.join(differentiation['suggested_approaches'][:2])}")
            else:
                print(f"   📊 {differentiation['category']} 첫 리뷰 작성")

            # 스타일 프로파일(무작위 각도) 생성
            style_angles = [
                "문제-해결(Problem→Insight→Solution)",
                "사용 시나리오 중심(누가 언제 어디서 어떻게)",
                "비교형(기존 제품 대비 개선/차이 3가지)",
                "핵심 스펙 숫자 강조(수치·치수·용량·소재 등 3개 이상)",
                "TIP 제공형(구매/사용/관리 팁 3가지)"
            ]
            chosen_angle = random.choice(style_angles)
            banned_phrases = [
                "직접 사용해보니 정말 만족스러웠어요",
                "제 솔직한 경험을 공유하고 싶어서 이렇게 후기를 남깁니다",
                "물론 완벽한 제품은 없듯이, 아쉬운 부분도 있었어요",
                "하지만 전체적으로 봤을 때 큰 단점은 아니었고, 사용하는 데 큰 불편함은 없었습니다"
            ]
            
            # 이미지 개수에 따른 글 구조 결정
            if image_count == 1:
                # 1개: 자유 후기
                print(f"   📊 이미지 1개 → 자유 후기 스타일 (단일)")
                return self._generate_free_style_content(title, price, description, image_count)
            elif image_count == 2:
                # 2개: 콜라주 1개 → 자유 후기
                print(f"   📊 이미지 2개 → 자유 후기 스타일 (콜라주 1개)")
                return self._generate_free_style_with_collage(title, price, description, image_count)
            elif image_count == 3:
                # 3개: 단일 3개 → 장점 3개
                advantage_count = 3
                print(f"   📊 이미지 3개 → 장점 3개 (단일 배치)")
            elif image_count == 4:
                # 4개: 콜라주 2개 → 장점 2개
                advantage_count = 2
                print(f"   📊 이미지 4개 → 장점 2개 (콜라주)")
            elif image_count == 5:
                # 5개: 콜라주 2개 + 단일 1개 → 장점 3개
                advantage_count = 3
                print(f"   📊 이미지 5개 → 장점 3개 (콜라주 2개 + 단일 1개)")
            else:  # 6개 이상
                # 6개+: 콜라주 3개 → 장점 3개
                advantage_count = 3
                print(f"   📊 이미지 {image_count}개 → 장점 3개 (콜라주 최대 3개)")
            
            # 장점 섹션 동적 생성
            advantages_template = ""
            
            if image_count == 3:
                # 3개: 단일 이미지 3개
                for i in range(3):
                    advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{i+1}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
            elif image_count == 4:
                # 4개: 콜라주 2개
                for i in range(2):
                    img1 = i * 2 + 1
                    img2 = i * 2 + 2
                    advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{img1},{img2}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
            elif image_count == 5:
                # 5개: 콜라주 2개 + 단일 1개
                for i in range(2):
                    img1 = i * 2 + 1
                    img2 = i * 2 + 2
                    advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{img1},{img2}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
                # 마지막 단일 이미지
                advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 3 - 제품 설명 기반 구체적 장점]

[IMAGE:5]

[TEXT]
[장점 3에 대한 구체적 경험담 250-350자]

"""
            else:  # 6개 이상
                # 6개+: 콜라주 3개
                for i in range(3):
                    img1 = i * 2 + 1
                    img2 = i * 2 + 2
                    if img2 <= image_count:
                        advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{img1},{img2}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
            
            # 이미지 로드 (Vision API용)
            product_images = []
            if image_files:
                from PIL import Image
                print(f"   📸 상품 이미지 {len(image_files)}개 로드 중...")
                for img_path in image_files[:6]:  # 최대 6개만 사용 (토큰 절약)
                    try:
                        img = Image.open(img_path)
                        product_images.append(img)
                    except Exception as e:
                        print(f"      ⚠️ 이미지 로드 실패 ({img_path}): {e}")
                        continue
                print(f"   ✅ {len(product_images)}개 이미지 로드 완료")

            # 프롬프트 생성 (Vision API 버전 - 이미지 분석 지침 포함)
            image_analysis_instruction = ""
            if product_images:
                image_analysis_instruction = f"""
🔍 이미지 분석 지침 (매우 중요!):
첨부된 {len(product_images)}개의 이미지는 상품 이미지들입니다.
이 이미지들을 분석하여 아래 정보를 추출하세요:

✅ 포함할 정보:
- 제품의 실제 외관, 디자인, 색상
- 제품의 기능, 특징, 스펙 (크기, 무게, 용량, 소재 등)
- 사용 방법, 활용 팁
- 제품의 장점, 효과, 성능
- 구성품, 패키징

이미지에서 확인한 내용을 바탕으로 더 구체적이고 생생한 후기를 작성하세요.
"""

            # 차별화 지시 생성
            differentiation_instruction = f"""
🎯 차별화 전략 (매우 중요!):
{differentiation['differentiation_tip']}

최근 사용된 접근 방식: {', '.join(differentiation['recent_approaches']) if differentiation['recent_approaches'] else '없음'}
이번에 추천하는 접근 방식: {', '.join(differentiation['suggested_approaches'][:2])}

⚠️ 같은 카테고리 제품이라도 매번 다른 각도로 작성해야 합니다!
- 첫 번째 리뷰: 소재/촉감 중심
- 두 번째 리뷰: 크기/용량 중심
- 세 번째 리뷰: 사용 편의성 중심
- 네 번째 리뷰: 디자인/색상 중심
이런 식으로 계속 다양하게 접근하세요.
"""

            prompt = f"""
당신은 네이버 블로그 전문 리뷰어입니다. 아래 제품 후기를 작성하세요.

제품명: {title}
가격: {price}
제품 설명: {description}

{image_analysis_instruction}

{differentiation_instruction}

작성 관점(랜덤으로 선택됨): {chosen_angle}

⚠️ 네이버 알고리즘 최적화 규칙:

【C-Rank 신뢰도】
- 제품명 + 기능 + 체험을 구체적으로
- 감각어 필수: 부드러운 촉감, 딸깍하는 소리, 은은한 향
- 소재/치수/용량 등 3가지 이상 명시

【D.I.A 체류시간】
- 각 문단 250자 이상 (30초 체류 목표)
- 소제목으로 단락 구분

⚠️ 중요 규칙:
1. 반드시 아래 형식 그대로 출력 (대괄호 포함!)
2. [TEXT], [QUOTE:VERTICAL], [QUOTE:UNDERLINE], [IMAGE:x,y], [LINK] 태그 정확히 사용
3. 다양한 종결어미 사용 (~했어요, ~더라고요, ~네요, ~습니다, ~거든요, ~있습니다, ~됩니다)
4. "~요"로 끝나는 문장이 연속 3번 이상 나오지 않도록 주의
5. 특수문자 적극 활용 (쉼표, 느낌표!, 물음표?, 괄호(), 따옴표"")
6. 감탄문과 의문문을 적절히 섞어서 생동감 있게
7. 조사 선택지 절대 금지! (을/를), (이/가), (은/는) 같은 표현 사용하지 말 것
8. 제품명 뒤 조사는 자연스럽게 하나만 선택 (예: "이불을", "멀티탭이")
9. 각 문단 250자 이상 작성 (체류시간 30초 이상 확보)
10. 이모티콘 적극 활용 (✨⭐💯👍🔥💝✔️👏❤️💪🎁🎉) - 문장 끝이나 강조할 부분에 자연스럽게
11. 자연스러운 표현 사용 ("역시", "완전", "진짜", "꼭" 등을 적절히)
12. 숫자 나열(첫째, 둘째) 사용 금지
13. 아래 문장을 그대로 복사/변형하여 쓰지 말 것(금지 문구): {' / '.join(banned_phrases)}
14. 인트로/아웃트로는 항상 다른 표현으로, 제품의 구체적 특징 3가지를 문장 안에 녹여 쓸 것 (소재·치수·용량·모델명·기능 등)

📌 출력 형식 (정확히 따라주세요):

[TEXT]
이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 판매 발생 시 수수료를 제공받습니다.

[QUOTE:VERTICAL]
{title} 솔직 후기

[TEXT]
고정 관용구 없이, 상황을 가정한 생동감 있는 인트로를 3~4문장으로 작성하세요. 
예: 어떤 문제를 겪다가 이 제품을 선택하게 된 계기, 첫 사용 순간의 디테일한 관찰 포인트(소재/만듦새/소리/무게/질감/온도감 등), 수치나 비교 표현 1개 이상 포함.

{advantages_template}

[TEXT]
사용 중 실제로 불편했거나 아쉬웠던 점 1~2가지를 구체적으로 작성하세요(객관적 디테일·상황·빈도 포함). 단, 금지 문구는 사용하지 마세요.

[TEXT]
총평은 3~4문장으로: 누구에게 특히 적합한지, 구매 시 체크포인트 1개, 가격 정보 또는 보증/AS 여부 등 실용 정보를 한 문장 포함.

💡 관련 글 보기: 더 궁금한 내용이 있다면 이전 리뷰도 확인해보세요
🤔 궁금한 점이 있으시면 댓글로 남겨주세요
⭐ 도움이 되셨다면 공감 한 번 부탁드려요

제품 정보 확인 👇

[LINK]

위 형식 그대로 작성하세요.

---

📌 강조 키워드 추출 (본문 작성 완료 후):

위에서 작성한 본문에서 강조하면 좋을 키워드/구절을 추출하여 JSON 형식으로 출력하세요.

강조 규칙:
1. 도입부(intro): 0-2개 선택적 강조
2. 장점 섹션(advantage_1, advantage_2, advantage_3): 각 섹션마다 2-4개씩 골고루 분산
3. 단점 섹션(disadvantage): 절대 강조 금지!
4. 마무리(conclusion): 0-2개 선택적 강조

스타일 선택 기준:
- 제품 핵심 특징/스펙 → "bold_font" (굵게+글자색, 강한 강조)
- 긍정적 표현/느낌 → "bg_color" (배경색, 형광펜 효과)
- 숫자/용량/치수 → "font_size" (글자 크기 변경)
- 일반 강조 → "bold" (굵게만)
- 브랜드명/제품명 → "font_color" (글자색만)

주의사항:
- 본문에 실제로 존재하는 텍스트만 추출
- 2-15글자 길이의 키워드/구절
- 단어 조합도 가능 (예: "가성비 좋은 완벽한 정수기")
- 전체 10-20개 정도

JSON 형식 예시:
```json
{{
  "highlights": [
    {{"text": "LG 퓨리케어 에어워셔", "style": "bold_font", "section": "intro"}},
    {{"text": "자연기화식 방식", "style": "font_color", "section": "advantage_1"}},
    {{"text": "백화현상 없음", "style": "bg_color", "section": "advantage_1"}},
    {{"text": "5L 대용량", "style": "bold", "section": "advantage_2"}},
    {{"text": "25dB 조용함", "style": "font_size", "section": "advantage_3"}},
    {{"text": "강력 추천합니다", "style": "bold_font", "section": "conclusion"}}
  ]
}}
```

본문 다음에 ```json으로 시작하는 JSON만 출력하세요:
"""
            
            gen_config = genai.GenerationConfig(temperature=0.95, top_p=0.9)

            # Vision API 호출 (이미지가 있으면 함께 전송)
            if product_images:
                print(f"   🤖 Gemini Vision API 호출 중...")
                print(f"      - 텍스트 정보: {len(description)}자")
                print(f"      - 이미지 개수: {len(product_images)}개")
                # 프롬프트 + 이미지들을 함께 전송
                content_parts = [prompt] + product_images
                response = model.generate_content(content_parts, generation_config=gen_config)
            else:
                print(f"   🤖 Gemini API 호출 중 (텍스트만)...")
                response = model.generate_content(prompt, generation_config=gen_config)

            ai_response = response.text.strip()
            
            # 본문과 JSON 분리
            import json
            import re
            
            # JSON 부분 찾기
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group(1)
                    highlights_data = json.loads(json_str)
                    highlights = highlights_data.get('highlights', [])
                    print(f"   ✅ AI 키워드 추출: {len(highlights)}개")
                except Exception as e:
                    print(f"   ⚠️ JSON 파싱 실패: {e}")
                    highlights = []
            else:
                print(f"   ⚠️ JSON을 찾을 수 없음")
                highlights = []
            
            # JSON 제거하고 본문만
            ai_content = re.sub(r'```json.*?```', '', ai_response, flags=re.DOTALL).strip()
            ai_content = self._soft_avoid_phrases(ai_content)
            
            print(f"✅ AI 글 생성 완료 ({len(ai_content)}자)")

            # 태그 생성
            tags = self._generate_tags(title, description)

            # 히스토리 저장 (사용된 접근 각도 포함)
            try:
                suggested_approach = differentiation['suggested_approaches'][0] if differentiation['suggested_approaches'] else None
                history_manager.save_history(title, ai_content, suggested_approach)
            except Exception as e:
                print(f"   ⚠️ 히스토리 저장 실패 (무시): {e}")

            return {
                'content': ai_content,
                'tags': tags,
                'highlights': highlights
            }
            
        except Exception as e:
            print(f"❌ AI 글 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_free_style_content(self, title, price, description, image_count):
        """이미지 1개 이하일 때 자유 후기 스타일 생성"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("   🤖 모델: gemini-2.5-pro")
            except:
                model = genai.GenerativeModel('gemini-2.5-flash')
                print("   🤖 모델: gemini-2.5-flash (백업)")
            
            # 랜덤 스타일 각도 및 금지 문구
            style_angles = [
                "문제-해결(Problem→Insight→Solution)",
                "사용 시나리오 중심(누가 언제 어디서 어떻게)",
                "비교형(기존 제품 대비 개선/차이 3가지)",
                "핵심 스펙 숫자 강조(수치·치수·용량·소재 등 3개 이상)",
                "TIP 제공형(구매/사용/관리 팁 3가지)"
            ]
            chosen_angle = random.choice(style_angles)
            banned_phrases = [
                "직접 사용해보니 정말 만족스러웠어요",
                "제 솔직한 경험을 공유하고 싶어서 이렇게 후기를 남깁니다",
                "물론 완벽한 제품은 없듯이, 아쉬운 부분도 있었어요",
                "하지만 전체적으로 봤을 때 큰 단점은 아니었고, 사용하는 데 큰 불편함은 없었습니다"
            ]

            # 자유 후기 프롬프트
            prompt = f"""
당신은 네이버 블로그 전문 리뷰어입니다. 아래 제품 후기를 작성하세요.

제품명: {title}
가격: {price}
제품 설명: {description}

작성 관점(랜덤): {chosen_angle}

⚠️ 중요 규칙:
1. 반드시 아래 형식 그대로 출력 (대괄호 포함!)
2. [TEXT], [QUOTE:VERTICAL], [IMAGE:1], [LINK] 태그 정확히 사용
3. 다양한 종결어미 사용 (~했어요, ~더라고요, ~네요, ~습니다, ~거든요)
4. "~요"로 끝나는 문장이 연속 3번 이상 나오지 않도록 주의
5. 특수문자 적극 활용 (쉼표, 느낌표!, 물음표?, 괄호())
6. 조사 선택지 절대 금지! (을/를), (이/가) 같은 표현 사용하지 말 것
7. 각 문단 200자 이상 작성
8. 이모티콘 적절 활용 (✨⭐💯👍🔥💝✔️👏❤️💪🎁🎉) - 문장 끝이나 강조할 부분만
9. 구매욕을 자극하는 표현 사용 가능하나 남용 금지
10. 숫자 나열(첫째, 둘째) 사용 금지
11. 아래 금지 문구를 그대로/유사하게 쓰지 말 것: {' / '.join(banned_phrases)}
12. 인트로/아웃트로는 항상 다른 표현으로, 제품의 구체적 특징 3가지를 문장 안에 녹여 쓸 것 (소재·치수·용량·모델명·기능 등)

📌 출력 형식 (정확히 따라주세요):

[TEXT]
이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 판매 발생 시 수수료를 제공받습니다.

[QUOTE:VERTICAL]
{title} 솔직 후기

[TEXT]
고정 관용구 없이, 실제 사용 맥락을 가정한 인트로 3~4문장을 작성하세요. 
수치/비교/감각 표현을 최소 1개 포함하고, 금지 문구는 사용 금지.

[TEXT]
첫인상/개봉/설치/사용 첫날의 디테일을 3~4문장으로 묘사하세요(소재/만듦새/무게/질감/소리/온기 등 구체 표현 포함).

{"[IMAGE:1]" if image_count >= 1 else ""}

[TEXT]
며칠 동안 사용해본 결과, 정말 만족스럽습니다! 처음 걱정했던 부분들은 전혀 문제가 없었고, 오히려 예상보다 더 좋은 점들이 많았어요. 사용하면서 불편한 점은 거의 없었고, 일상생활에서 정말 유용하게 쓰고 있습니다. 가격 대비 이 정도 품질이면 충분히 만족스러워요.

{"[IMAGE:2]" if image_count >= 2 else ""}

[TEXT]
디자인도 정말 마음에 들고, 실용성도 뛰어나서 만족도가 높습니다! 여러 면에서 기대 이상이었어요. 특히 세세한 부분까지 잘 만들어져서 사용할 때마다 만족감이 듭니다.

{"[IMAGE:3]" if image_count >= 3 else ""}

[TEXT]
아쉬운 점 1~2가지를 구체적으로(상황·원인·빈도 포함) 쓰고, 대안/회피 팁 1개를 제시하세요. 금지 문구 사용 금지.

[TEXT]
총평: 어떤 사용자에게 특히 적합한지, 가격/보증/AS/배송 등 실용 정보 1개, 구매 체크포인트 1개를 포함해 3~4문장으로 작성하세요.

제품 정보 확인 👇

[LINK]

위 형식 그대로 작성하세요:
"""
            
            gen_config = genai.GenerationConfig(temperature=0.95, top_p=0.9)
            response = model.generate_content(prompt, generation_config=gen_config)
            ai_content = response.text.strip()
            ai_content = self._soft_avoid_phrases(ai_content)
            
            print(f"✅ AI 자유 후기 생성 완료 ({len(ai_content)}자)")
            
            # 태그 생성
            tags = self._generate_tags(title, description)
            
            return {
                'content': ai_content,
                'tags': tags
            }
            
        except Exception as e:
            print(f"❌ AI 자유 후기 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_free_style_with_collage(self, title, price, description, image_count):
        """이미지 2개일 때 콜라주 사용하는 자유 후기 스타일 생성"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.gemini_api_key)
            
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("   🤖 모델: gemini-2.5-pro")
            except:
                model = genai.GenerativeModel('gemini-2.5-flash')
                print("   🤖 모델: gemini-2.5-flash (백업)")
            
            # 랜덤 스타일 + 금지 문구
            style_angles = [
                "문제-해결(Problem→Insight→Solution)",
                "사용 시나리오 중심(누가 언제 어디서 어떻게)",
                "비교형(기존 제품 대비 개선/차이 3가지)",
                "핵심 스펙 숫자 강조(수치·치수·용량·소재 등 3개 이상)",
                "TIP 제공형(구매/사용/관리 팁 3가지)"
            ]
            chosen_angle = random.choice(style_angles)
            banned_phrases = [
                "직접 사용해보니 정말 만족스러웠어요",
                "제 솔직한 경험을 공유하고 싶어서 이렇게 후기를 남깁니다",
                "물론 완벽한 제품은 없듯이, 아쉬운 부분도 있었어요",
                "하지만 전체적으로 봤을 때 큰 단점은 아니었고, 사용하는 데 큰 불편함은 없었습니다"
            ]

            # 자유 후기 프롬프트 (콜라주 사용)
            prompt = f"""
당신은 네이버 블로그 전문 리뷰어입니다. 아래 제품 후기를 작성하세요.

제품명: {title}
가격: {price}
제품 설명: {description}

작성 관점(랜덤): {chosen_angle}

⚠️ 중요 규칙:
1. 반드시 아래 형식 그대로 출력 (대괄호 포함!)
2. [TEXT], [QUOTE:VERTICAL], [IMAGE:1,2], [LINK] 태그 정확히 사용
3. 다양한 종결어미 사용 (~했어요, ~더라고요, ~네요, ~습니다, ~거든요)
4. "~요"로 끝나는 문장이 연속 3번 이상 나오지 않도록 주의
5. 특수문자 적극 활용 (쉼표, 느낌표!, 물음표?, 괄호())
6. 조사 선택지 절대 금지! (을/를), (이/가) 같은 표현 사용하지 말 것
7. 각 문단 200자 이상 작성
8. 이모티콘 적절 활용 (✨⭐💯👍🔥💝✔️👏❤️💪🎁🎉)
9. 구매욕을 자극하는 표현은 남용 금지
10. 숫자 나열(첫째, 둘째) 사용 금지
11. 아래 금지 문구를 그대로/유사하게 쓰지 말 것: {' / '.join(banned_phrases)}
12. 인트로/아웃트로는 항상 다른 표현으로, 제품의 구체적 특징 3가지를 문장 안에 녹여 쓸 것

📌 출력 형식 (정확히 따라주세요):

[TEXT]
이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 판매 발생 시 수수료를 제공받습니다.

[QUOTE:VERTICAL]
{title} 솔직 후기

[TEXT]
고정 관용구 없이, 상황을 가정한 인트로 3~4문장을 작성하세요(수치/비교/감각 묘사 포함, 금지 문구 금지).

[TEXT]
첫인상~초기사용 단계의 디테일을 3~4문장으로 묘사하세요(소재/만듦새/무게/질감/소리/온기 등 구체 표현 포함).

[IMAGE:1,2]

[TEXT]
콜라주 이미지를 기준으로, 사용성·편의·가성비 등 핵심 장점을 구체적으로 적되 과장 표현은 줄이고 사실 기반으로 3~4문장 작성.

[TEXT]
아쉬운 점 1~2가지를 구체적으로(상황·원인·빈도 포함) 쓰고, 대안/회피 팁 1개를 제시하세요. 금지 문구 사용 금지.

[TEXT]
총평: 어떤 사용자에게 특히 적합한지, 가격/보증/AS/배송 등 실용 정보 1개, 구매 체크포인트 1개를 포함해 3~4문장으로 작성하세요.

제품 정보 확인 👇

[LINK]

위 형식 그대로 작성하세요:
"""
            
            gen_config = genai.GenerationConfig(temperature=0.95, top_p=0.9)
            response = model.generate_content(prompt, generation_config=gen_config)
            ai_content = response.text.strip()
            ai_content = self._soft_avoid_phrases(ai_content)
            
            print(f"✅ AI 자유 후기 생성 완료 (콜라주) ({len(ai_content)}자)")
            
            # 태그 생성
            tags = self._generate_tags(title, description)
            
            return {
                'content': ai_content,
                'tags': tags
            }
            
        except Exception as e:
            print(f"❌ AI 자유 후기 생성 실패 (콜라주): {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_tags(self, title, description):
        """AI 기반 제품 특성 태그 생성"""
        print("   🏷️  AI 태그 생성 중...")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
                print("   🤖 모델: gemini-2.5-pro")
            except:
                model = genai.GenerativeModel('gemini-2.5-flash')
                print("   🤖 모델: gemini-2.5-flash (백업)")
            
            # AI에게 태그 생성 요청
            prompt = f"""
아래 제품 정보를 보고 네이버 블로그 해시태그를 정확히 30개 생성하세요.

제품명: {title}
제품 설명: {description[:300]}

⚠️ 태그 생성 규칙:
1. 제품 특성과 직접 관련된 롱테일 키워드 위주 (25개)
2. "제품카테고리+특성" 조합 (예: 이불추천, 겨울이불추천, 따뜻한겨울이불)
3. 사용자 검색 의도 반영 (예: 알러지있는사람이불, 추위많이타는이불)
4. 브랜드명 활용 (예: 슬라운드이불)
5. 제품 장점 키워드 (예: 부드러운이불, 포근한이불)
6. 각 태그는 2-8글자로 구성
7. 띄어쓰기 없이 붙여쓰기

📌 출력 형식 (정확히 이렇게!):
태그1,태그2,태그3,...태그30

예시:
이불추천,겨울이불추천,따뜻한겨울이불,침구류세트,알러지케어이불

태그만 출력하세요 (설명 없이):
"""
            
            response = model.generate_content(prompt)
            ai_tags_text = response.text.strip()
            
            # 태그 파싱 (쉼표로 구분)
            tags = [tag.strip().replace('#', '') for tag in ai_tags_text.split(',')]
            tags = [tag for tag in tags if tag and len(tag) >= 2]
            
            # AI 태그는 최대 30개로
            if len(tags) > 30:
                tags = tags[:30]
            
            # 검색량 높은 일반 태그 추가 (10개)
            high_traffic_tags = [
                '추천', '후기', '리뷰', '가성비', '인기',
                '베스트', '구매후기', '사용후기', '솔직후기', '꿀템'
            ]
            
            for tag in high_traffic_tags:
                if tag not in tags:
                    tags.append(tag)
            
            # 정확히 40개로 맞추기
            if len(tags) < 40:
                # 부족하면 추가 일반 태그
                extra_tags = ['최저가', '할인', '특가', '실사용후기', '추천템']
                for tag in extra_tags:
                    if tag not in tags and len(tags) < 40:
                        tags.append(tag)
            
            # 태그 3-5개로 제한 (네이버 가이드 준수)
            tag_count = random.randint(4, 10)
            tags = tags[:tag_count]
            
            print(f"   ✅ AI 태그 {len(tags)}개 생성")
            print(f"      제품 특성: {', '.join(tags[:5])}...")
            print(f"      일반 키워드: 추천, 후기, 리뷰...")
            return tags
            
        except Exception as e:
            print(f"   ⚠️ AI 태그 생성 실패, 기본 태그 사용: {e}")
            # 폴백: 간단한 태그
            return ['추천', '후기', '리뷰', '가성비', '인기', '베스트', '구매후기', '사용후기', '솔직후기', '좋은제품']
    
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
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()


def main():
    """메인 함수"""
    print("="*60)
    print("🤖 네이버 블로그 자동화 프로그램")
    print("="*60)
    
    # 설정
    blog_id = input("\n📝 블로그 ID: ").strip()
    naver_id = input("🔐 네이버 ID: ").strip()
    naver_pw = input("🔑 네이버 PW: ").strip()
    gemini_api_key = input("🤖 Gemini API Key: ").strip()
    chrome_profile = input("🌐 Chrome 프로필 이름 (default): ").strip() or 'default'
    shopping_url = input("🛒 쇼핑 URL (naver.me): ").strip()

    # 자동화 시작
    bot = NaverBlogAutomation(blog_id, naver_id, naver_pw, gemini_api_key, chrome_profile)
    
    try:
        # 1. 브라우저 시작
        bot.start_browser()
        
        # 2. 로그인
        if not bot.login():
            print("❌ 로그인 실패")
            return
        
        # 3. 제품 정보 추출
        product_info = bot.extract_product_info(shopping_url)
        if not product_info:
            print("❌ 제품 정보 추출 실패")
            return
        
        # 4. 이미지 다운로드
        image_files = bot.download_images(product_info['images'])
        if not image_files:
            print("❌ 이미지 다운로드 실패 - 최소 1개 이상 필요합니다")
            return
        
        # 5. AI 글 생성
        ai_content = bot.generate_ai_content(product_info)
        if not ai_content:
            print("❌ AI 글 생성 실패")
            return
        
        # 6. 블로그 글 작성
        if bot.write_blog_post(product_info['title'], ai_content, image_files, shopping_url):
            print("\n✅ 블로그 글 작성 완료!")
            print("\n⏸️  브라우저에서 확인 후 발행해주세요...")
            input("Enter를 누르면 종료됩니다...")
        else:
            print("❌ 블로그 글 작성 실패")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        input("Enter를 누르면 종료됩니다...")
    
    finally:
        bot.close()


if __name__ == "__main__":
    main()

