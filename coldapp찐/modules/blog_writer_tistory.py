"""
티스토리 블로그 작성 모듈
- 티스토리 OpenAPI 사용
- REST API로 깔끔하게 포스팅
- 네이버 형식 → 티스토리 HTML 변환
"""

import requests
import time
import re
from typing import List, Dict, Optional


class TistoryBlogWriter:
    """티스토리 블로그 작성 클래스"""

    BASE_URL = "https://www.tistory.com/apis"

    def __init__(self, access_token: str, blog_name: str):
        """
        초기화

        Args:
            access_token: 티스토리 OAuth Access Token
            blog_name: 블로그 이름 (예: myblog.tistory.com의 'myblog')
        """
        self.access_token = access_token
        self.blog_name = blog_name

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        이미지 업로드

        Args:
            image_path: 이미지 파일 경로

        Returns:
            str: 업로드된 이미지 URL (실패 시 None)
        """
        print(f"   📤 티스토리 이미지 업로드: {image_path}")

        try:
            url = f"{self.BASE_URL}/post/attach"

            params = {
                "access_token": self.access_token,
                "blogName": self.blog_name,
                "output": "json"
            }

            with open(image_path, 'rb') as f:
                files = {'uploadedfile': f}
                response = requests.post(url, params=params, files=files, timeout=30)

            result = response.json()

            if result.get("tistory", {}).get("status") == "200":
                image_url = result["tistory"]["url"]
                # HTTP를 HTTPS로 변경
                image_url = image_url.replace("http://", "https://")
                print(f"      ✅ 업로드 완료: {image_url}")
                return image_url
            else:
                error_msg = result.get("tistory", {}).get("error_message", "Unknown error")
                print(f"      ❌ 업로드 실패: {error_msg}")
                return None

        except Exception as e:
            print(f"      ❌ 이미지 업로드 오류: {e}")
            return None

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

        # [TEXT] 처리
        text_pattern = r'\[TEXT\]\s*(.*?)(?=\[|$)'
        texts = re.findall(text_pattern, ai_content, re.DOTALL)

        # [QUOTE:VERTICAL] 처리 - 세로 인용구
        quote_vertical_pattern = r'\[QUOTE:VERTICAL\]\s*(.*?)(?=\[|$)'
        quote_verticals = re.findall(quote_vertical_pattern, ai_content, re.DOTALL)

        # [QUOTE:UNDERLINE] 처리 - 밑줄 인용구
        quote_underline_pattern = r'\[QUOTE:UNDERLINE\]\s*(.*?)(?=\[|$)'
        quote_underlines = re.findall(quote_underline_pattern, ai_content, re.DOTALL)

        # [IMAGE:x,y] 처리
        image_pattern = r'\[IMAGE:([\d,]+)\]'
        image_tags = re.findall(image_pattern, ai_content)

        # [LINK] 처리
        link_pattern = r'\[LINK\]'

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
                    html_parts.append(f'<p style="line-height: 1.8;">{content}</p>')

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

    def write_post(
        self,
        title: str,
        ai_result: Dict,
        image_files: List[str],
        shopping_url: str,
        visibility: int = 3,
        category: int = 0
    ) -> Optional[Dict]:
        """
        티스토리에 글 작성

        Args:
            title: 글 제목
            ai_result: AI 생성 결과 {'content': '...', 'tags': [...]}
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
            visibility: 발행 상태 (0: 비공개, 1: 보호, 3: 발행)
            category: 카테고리 ID

        Returns:
            dict: API 응답 (성공 시) 또는 None (실패 시)
        """
        print(f"\n📝 티스토리 글 작성 중...")
        print(f"   제목: {title}")

        try:
            # 1. 이미지 업로드
            print(f"\n📤 이미지 업로드 중 ({len(image_files)}개)...")
            image_urls = []

            for i, img_path in enumerate(image_files, 1):
                print(f"   [{i}/{len(image_files)}] 업로드 중...")
                url = self.upload_image(img_path)
                if url:
                    image_urls.append(url)
                time.sleep(0.5)  # Rate limiting

            print(f"   ✅ {len(image_urls)}개 이미지 업로드 완료")

            # 2. 네이버 형식 → 티스토리 HTML 변환
            print(f"\n🔄 HTML 변환 중...")
            html_content = self._convert_naver_format_to_html(
                ai_result['content'],
                image_urls,
                shopping_url
            )

            # 3. 태그 생성
            tags = ','.join(ai_result.get('tags', [])[:10])  # 최대 10개

            # 4. 글 작성 API 호출
            print(f"\n📤 티스토리 API 호출 중...")
            url = f"{self.BASE_URL}/post/write"

            data = {
                "access_token": self.access_token,
                "output": "json",
                "blogName": self.blog_name,
                "title": title,
                "content": html_content,
                "visibility": visibility,
                "category": category,
                "tag": tags
            }

            response = requests.post(url, data=data, timeout=30)
            result = response.json()

            # 5. 결과 확인
            if result.get("tistory", {}).get("status") == "200":
                post_id = result["tistory"]["postId"]
                post_url = result["tistory"]["url"]

                print(f"\n✅ 티스토리 글 발행 완료!")
                print(f"   글 ID: {post_id}")
                print(f"   URL: {post_url}")

                return result
            else:
                error_msg = result.get("tistory", {}).get("error_message", "Unknown error")
                print(f"\n❌ 티스토리 글 작성 실패: {error_msg}")
                return None

        except Exception as e:
            print(f"\n❌ 티스토리 글 작성 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_connection(self) -> bool:
        """
        티스토리 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            url = f"{self.BASE_URL}/blog/info"

            params = {
                "access_token": self.access_token,
                "output": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            result = response.json()

            if result.get("tistory", {}).get("status") == "200":
                print("✅ 티스토리 연결 성공")
                return True
            else:
                print("❌ 티스토리 연결 실패")
                return False

        except Exception as e:
            print(f"❌ 티스토리 연결 오류: {e}")
            return False


# OAuth 토큰 발급 헬퍼 함수들
def get_authorization_url(client_id: str, redirect_uri: str, state: str = "random_state") -> str:
    """
    OAuth 인증 URL 생성

    Args:
        client_id: 티스토리 앱 Client ID
        redirect_uri: Callback URL
        state: CSRF 방지용 랜덤 문자열

    Returns:
        str: 인증 URL
    """
    return (
        f"https://www.tistory.com/oauth/authorize?"
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&state={state}"
    )


def get_access_token(client_id: str, client_secret: str, redirect_uri: str, code: str) -> Optional[str]:
    """
    Authorization Code로 Access Token 발급

    Args:
        client_id: 티스토리 앱 Client ID
        client_secret: 티스토리 앱 Secret Key
        redirect_uri: Callback URL
        code: Authorization Code

    Returns:
        str: Access Token (실패 시 None)
    """
    try:
        url = "https://www.tistory.com/oauth/access_token"

        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code"
        }

        response = requests.get(url, params=params, timeout=10)

        # 응답 형식: access_token=xxxxx
        if "access_token=" in response.text:
            access_token = response.text.split("=")[1]
            return access_token
        else:
            print(f"❌ 토큰 발급 실패: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 토큰 발급 오류: {e}")
        return None
