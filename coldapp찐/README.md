# 네이버 블로그 자동화 (Vision API 버전) 🚀

상품 상세 설명 이미지를 Gemini Vision API로 분석하여 더 풍부한 블로그 글을 작성합니다!

## ✨ 주요 개선 사항

### 이전 버전
- ❌ 텍스트 설명만 활용
- ❌ 이미지 속 정보 활용 불가

### Vision 버전 ⭐
- ✅ **상세 설명 이미지 분석** (Gemini Vision)
- ✅ **제품 정보만 추출** (배송/이벤트 자동 제외)
- ✅ **모듈화된 구조** (유지보수 쉬움)
- ✅ **토큰 최적화** (최대 10개 이미지만 사용)

---

## 📂 프로젝트 구조

```
프로젝트/
├── main_gui4.py                    # GUI 메인 (기존 파일)
├── naver_blog_automation.py        # 메인 클래스 (새 버전)
├── modules/
│   ├── __init__.py
│   ├── browser_handler.py          # 브라우저, 로그인
│   ├── product_extractor.py        # 상품 정보 추출 ⭐
│   ├── image_handler.py            # 이미지 다운로드 ⭐
│   ├── ai_generator.py             # AI 글 생성 (Vision) ⭐⭐⭐
│   ├── blog_writer.py              # 블로그 작성
│   └── utils.py                    # 유틸리티
├── firebase_auth.py                # Firebase 인증 (기존)
└── assets/                         # 아이콘 (기존)
```

---

## 🔧 설치 방법

### 1. 기존 파일 백업
```bash
# 기존 naver_blog_automation.py 백업
mv naver_blog_automation.py naver_blog_automation_old.py
```

### 2. 새 파일 복사
```bash
# 압축 해제
tar -xzf naver_blog_vision_modules.tar.gz

# 파일 확인
ls -la modules/
```

### 3. 필요한 라이브러리 확인
```bash
pip install Pillow  # 이미지 처리 (Vision API용)
```

---

## 🚀 사용 방법

### GUI에서 사용 (기존 방식)
```bash
python main_gui4.py
```

**변경 사항 없음!** GUI는 자동으로 새 모듈을 사용합니다.

### 터미널에서 직접 사용
```bash
python naver_blog_automation.py
```

---

## 📊 작동 방식

### 1단계: 상품 정보 수집
```python
product_info = bot.extract_product_info(shopping_url)
```
- 상품명, 가격, 텍스트 설명
- **대표 이미지 URL** (기존)
- **상세 설명 이미지 URL** ⭐ 신규

### 2단계: 이미지 다운로드
```python
product_images, detail_images = bot.download_all_images(product_info)
```
- 대표 이미지: 블로그에 올릴 사진
- 상세 이미지: Vision API로 분석할 사진 (최대 10개)

### 3단계: AI 글 생성 (Vision)
```python
ai_result = bot.generate_ai_content(product_info, detail_images)
```
- Gemini Vision API가 상세 이미지를 "보고" 분석
- **제품 정보만 추출** (배송/이벤트 자동 제외)
- 자연스러운 블로그 후기 생성

### 4단계: 블로그 발행
```python
bot.write_blog_post(title, ai_result, product_images, shopping_url)
```

---

## 💡 주요 기능 상세

### ⭐ Vision API 이미지 분석
```python
# modules/ai_generator.py

# 상세 이미지를 Gemini에게 보여주고
detail_images = [Image.open(path) for path in detail_image_paths]

# 프롬프트로 "제품 정보만 추출"하도록 지시
prompt = """
🔍 이미지 분석 지침:
✅ 포함: 제품 기능, 스펙, 사용법
❌ 제외: 배송, 이벤트, 회사소개
"""

# Vision API 호출
response = model.generate_content([prompt] + detail_images)
```

### ⭐ 토큰 최적화
```python
# modules/product_extractor.py

# 상세 이미지 최대 10개로 제한
if len(detail_image_urls) > 10:
    return detail_image_urls[:10]
```

### ⭐ 모듈화된 구조
각 기능이 독립된 파일로 분리되어 수정이 쉽습니다:
- 이미지 처리만 수정 → `image_handler.py`
- AI 프롬프트 수정 → `ai_generator.py`
- 블로그 작성 방식 수정 → `blog_writer.py`

---

## 📈 비용 비교 (Gemini 2.5 Pro 기준)

| 항목 | 기존 | Vision 버전 | 차이 |
|------|------|-------------|------|
| 입력 토큰 | 1,000 | 2,000 | +1,000 |
| 출력 토큰 | 1,500 | 1,500 | 0 |
| **글 1개 비용** | **약 12원** | **약 13원** | **+1원** |
| 100개 작성 | 1,200원 | 1,330원 | +130원 |

**결론:** 비용 증가는 미미하지만, 품질은 크게 향상! 🎉

---

## 🔍 문제 해결

### 1. ModuleNotFoundError: No module named 'modules'
```bash
# modules 폴더가 naver_blog_automation.py와 같은 위치에 있는지 확인
ls -la
```

### 2. PIL 관련 오류
```bash
pip install Pillow
```

### 3. 이미지가 너무 많아서 느림
```python
# modules/product_extractor.py의 393번 줄 수정
return detail_image_urls[:5]  # 10 → 5로 변경
```

---

## 📝 코드 수정 가이드

### AI 프롬프트 수정
파일: `modules/ai_generator.py`  
함수: `_build_vision_prompt()`

```python
# 115번 줄 근처
prompt = f"""
당신은 네이버 블로그 전문 리뷰어입니다.

🔍 이미지 분석 지침:
✅ 포함할 정보:
- 제품 기능, 스펙
- [여기에 추가하고 싶은 내용]

❌ 제외할 정보:
- 배송, 이벤트
- [여기에 추가하고 싶은 내용]
"""
```

### 이미지 개수 조절
파일: `modules/product_extractor.py`  
함수: `_extract_detail_images()`

```python
# 393번 줄 근처
if len(detail_image_urls) > 10:
    return detail_image_urls[:10]  # 숫자 변경
```

### 다운로드 개수 조절
파일: `naver_blog_automation.py`  
함수: `download_all_images()`

```python
# 131번 줄 근처
detail_images = self.image_handler.download_detail_images(
    product_info['detail_images'],
    max_images=10  # 숫자 변경
)
```

---

## 🎯 다음 단계

1. ✅ **모듈화 완료**
2. ✅ **Vision API 통합 완료**
3. ✅ **제품 정보만 추출 완료**
4. 🔜 필요시 원본 파일의 고급 기능 추가:
   - 텍스트 스타일링 (굵게, 색상 등)
   - 이미지 콜라주
   - 더 정교한 태그 파싱

---

## 💬 문의

문제가 생기면 각 모듈 파일의 상단 주석을 참고하세요!
모든 함수에 상세한 설명이 포함되어 있습니다.

---

**🎉 Vision API로 더 풍부한 블로그 글을 만들어보세요!**
