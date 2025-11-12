"""
AI 콘텐츠 생성 모듈
- Gemini 2.5 Pro/Flash 활용
- Vision API로 상세 이미지 분석 ⭐ 신규
- 제품 정보만 추출 (배송/이벤트 제외) ⭐ 신규
- 태그 생성
"""

import random
import re
import json
from PIL import Image


class AIContentGenerator:
    """AI 콘텐츠 생성 클래스"""
    
    def __init__(self, gemini_api_key):
        """
        초기화
        
        Args:
            gemini_api_key: Gemini API 키
        """
        self.gemini_api_key = gemini_api_key
        self.model = None
        
    def initialize_model(self):
        """Gemini 모델 초기화"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.gemini_api_key)
        
        try:
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            print("   🤖 모델: gemini-2.5-pro")
        except:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("   🤖 모델: gemini-2.5-flash (백업)")
    
    def generate_content_with_vision(self, product_info, detail_image_paths):
        """
        Vision API를 활용하여 AI 콘텐츠 생성 ⭐ 핵심 함수
        
        Args:
            product_info: 제품 정보 dict
            detail_image_paths: 상세 설명 이미지 파일 경로 리스트
            
        Returns:
            dict: {
                'content': 생성된 블로그 글,
                'tags': 태그 리스트,
                'highlights': 강조할 키워드 리스트
            }
        """
        print(f"\n🤖 AI 글 생성 중 (Vision API 사용)...")
        
        try:
            # 모델 초기화
            if not self.model:
                self.initialize_model()
            
            title = product_info['title']
            price = product_info['price']
            description = product_info['description']
            image_count = len(product_info['images'])
            
            # 랜덤 스타일 각도
            style_angles = [
                "문제-해결(Problem→Insight→Solution)",
                "사용 시나리오 중심(누가 언제 어디서 어떻게)",
                "비교형(기존 제품 대비 개선/차이 3가지)",
                "핵심 스펙 숫자 강조(수치·치수·용량·소재 등 3개 이상)",
                "TIP 제공형(구매/사용/관리 팁 3가지)"
            ]
            chosen_angle = random.choice(style_angles)
            
            # 금지 문구
            banned_phrases = [
                "직접 사용해보니 정말 만족스러웠어요",
                "제 솔직한 경험을 공유하고 싶어서 이렇게 후기를 남깁니다",
                "물론 완벽한 제품은 없듯이, 아쉬운 부분도 있었어요",
                "하지만 전체적으로 봤을 때 큰 단점은 아니었고, 사용하는 데 큰 불편함은 없었습니다"
            ]
            
            # 이미지 개수에 따른 구조 결정
            advantages_template = self._build_advantages_template(image_count)
            
            # 상세 이미지 로드 (Vision용)
            detail_images = []
            if detail_image_paths:
                print(f"   📸 상세 이미지 {len(detail_image_paths)}개 로드 중...")
                for img_path in detail_image_paths:
                    try:
                        img = Image.open(img_path)
                        detail_images.append(img)
                    except Exception as e:
                        print(f"      ⚠️ 이미지 로드 실패 ({img_path}): {e}")
                        continue
                print(f"   ✅ {len(detail_images)}개 이미지 로드 완료")
            
            # 프롬프트 생성 (Vision 버전) ⭐
            prompt = self._build_vision_prompt(
                title, price, description, 
                advantages_template, chosen_angle, banned_phrases,
                len(detail_images)
            )
            
            # Vision API 호출 ⭐
            print(f"   🤖 Gemini Vision API 호출 중...")
            print(f"      - 텍스트 정보: {len(description)}자")
            print(f"      - 이미지 개수: {len(detail_images)}개")
            
            # 이미지와 함께 콘텐츠 생성
            if detail_images:
                # 프롬프트 + 이미지들을 함께 전송
                content_parts = [prompt] + detail_images
                response = self.model.generate_content(content_parts)
            else:
                # 이미지 없으면 텍스트만
                response = self.model.generate_content(prompt)
            
            ai_response = response.text.strip()
            
            # JSON 부분 분리
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            
            highlights = []
            if json_match:
                try:
                    json_str = json_match.group(1)
                    highlights_data = json.loads(json_str)
                    highlights = highlights_data.get('highlights', [])
                    print(f"   ✅ AI 키워드 추출: {len(highlights)}개")
                except Exception as e:
                    print(f"   ⚠️ JSON 파싱 실패: {e}")
            
            # JSON 제거하고 본문만
            ai_content = re.sub(r'```json.*?```', '', ai_response, flags=re.DOTALL).strip()
            
            # 상투적 문구 처리
            from .utils import StyleUtils
            ai_content = StyleUtils.soft_avoid_phrases(ai_content)
            
            print(f"✅ AI 글 생성 완료 ({len(ai_content)}자)")
            
            # 태그 생성
            tags = self._generate_tags(title, description)
            
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
    
    def _build_vision_prompt(self, title, price, description, advantages_template, 
                            chosen_angle, banned_phrases, image_count):
        """
        Vision API용 프롬프트 생성 ⭐
        상세 이미지를 보고 제품 정보만 추출하도록 명확히 지시
        """
        prompt = f"""
당신은 네이버 블로그 전문 리뷰어입니다. 아래 제품 후기를 작성하세요.

제품명: {title}
가격: {price}
제품 설명: {description}

작성 관점(랜덤으로 선택됨): {chosen_angle}

🔍 이미지 분석 지침 (매우 중요!): ⭐ 신규
첨부된 {image_count}개의 이미지는 상품 상세 페이지의 설명 이미지들입니다.
이 이미지들을 분석할 때 다음 규칙을 반드시 따르세요:

✅ 포함할 정보만 사용:
- 제품의 기능, 특징, 스펙 (크기, 무게, 용량, 소재 등)
- 사용 방법, 활용 팁
- 제품의 장점, 효과, 성능
- 디자인, 색상, 구성품

❌ 절대 포함하지 말 것:
- 배송 정보 (배송비, 배송 기간, 택배사 등)
- 반품/교환 안내
- 이벤트, 할인, 쿠폰 정보
- 회사 소개, 브랜드 스토리
- 고객센터, 연락처, AS 안내
- 구매 방법, 결제 방법
- 상품평, 리뷰 스크린샷

이미지 중 배송/이벤트/회사소개 관련 내용이 보이면 무시하고,
오직 제품 자체에 대한 정보만 활용해서 후기를 작성하세요.

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
        return prompt
    
    def _build_advantages_template(self, image_count):
        """이미지 개수에 따른 장점 섹션 템플릿 생성"""
        advantages_template = ""
        
        if image_count == 1 or image_count == 2:
            # 자유 형식
            return ""
        elif image_count == 3:
            for i in range(3):
                advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{i+1}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
        elif image_count == 4:
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
        else:  # 5개 이상
            for i in range(3):
                if i < 2:
                    img1 = i * 2 + 1
                    img2 = i * 2 + 2
                    advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 {i+1} - 제품 설명 기반 구체적 장점]

[IMAGE:{img1},{img2}]

[TEXT]
[장점 {i+1}에 대한 구체적 경험담 250-350자]

"""
                else:
                    advantages_template += f"""
[QUOTE:UNDERLINE]
[장점 3 - 제품 설명 기반 구체적 장점]

[IMAGE:5]

[TEXT]
[장점 3에 대한 구체적 경험담 250-350자]

"""
        
        return advantages_template
    
    def _generate_tags(self, title, description):
        """태그 생성"""
        # 제품명에서 키워드 추출
        keywords = []
        
        # 제목에서 단어 추출
        title_words = re.findall(r'[가-힣A-Za-z0-9]+', title)
        keywords.extend(title_words[:5])
        
        # 설명에서 명사 추출 (간단한 방식)
        desc_words = re.findall(r'[가-힣]{2,}', description)
        keywords.extend(desc_words[:3])
        
        # 중복 제거 및 정리
        tags = list(set(keywords))[:10]
        
        return tags
