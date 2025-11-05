# 티스토리 Selenium 자동 포스팅 가이드

## 개요

티스토리 Open API가 2024년 2월에 종료되면서, **Selenium 웹 자동화**를 이용한 새로운 포스팅 방식을 구현했습니다.

---

## 변경 사항

### ❌ 기존 방식 (API - 작동 중단)
```python
from modules import TistoryBlogWriter

writer = TistoryBlogWriter(
    access_token="...",
    blog_name="myblog"
)
```

**문제점:**
- 티스토리 Open API 종료 (2024.02)
- 더 이상 작동하지 않음

---

### ✅ 새로운 방식 (Selenium - 권장)
```python
from modules import TistorySeleniumWriter

writer = TistorySeleniumWriter(
    kakao_email="your_email@kakao.com",
    kakao_password="your_password",
    blog_name="myblog"
)

# 로그인
writer.login()

# 글 작성
writer.write_post(
    title="제목",
    ai_result=ai_result,
    image_files=image_files,
    shopping_url=shopping_url
)

# 종료
writer.close()
```

**장점:**
- 완전 무료
- 모든 티스토리 기능 사용 가능
- HTML 스타일 완벽 지원
- 네이버 블로그와 동일한 구조

---

## 설치 및 설정

### 1. 필수 패키지

```bash
pip install undetected-chromedriver
pip install selenium
```

### 2. 티스토리 전용 계정 생성 권장

**이유:**
- 카카오 2단계 인증(2FA) 문제 회피
- 자동화 전용 계정으로 안전하게 관리

**방법:**
1. 새로운 카카오 계정 생성
2. 해당 계정으로 티스토리 블로그 개설
3. 2단계 인증 비활성화

---

## 사용 방법

### 1. 단일 티스토리 포스팅

```python
from modules.blog_writer_tistory_selenium import TistorySeleniumWriter

# 초기화
writer = TistorySeleniumWriter(
    kakao_email="your_kakao_email@example.com",
    kakao_password="your_password",
    blog_name="mylittleshop"
)

# 로그인
if writer.login():
    # 글 작성
    success = writer.write_post(
        title="제품 리뷰 - 최고의 가성비",
        ai_result={
            'content': """
[TEXT] 제품 리뷰입니다.

[QUOTE:UNDERLINE] 주요 특징

[TEXT] 정말 좋은 제품이에요.

[IMAGE:1,2]

[LINK]
""",
            'tags': ['리뷰', '제품', '추천']
        },
        image_files=['image1.jpg', 'image2.jpg'],
        shopping_url='https://shopping.example.com'
    )

    if success:
        print("✅ 포스팅 완료!")

# 종료
writer.close()
```

---

### 2. 멀티 블로그 포스팅 (네이버 + 티스토리)

```python
from modules import MultiBlogManager, TistorySeleniumWriter
from naver_blog_automation import NaverBlogAutomation

# 네이버 설정
naver_writer = NaverBlogAutomation(
    blog_id="naver_blog_id",
    naver_id="naver_id",
    naver_pw="naver_pw",
    gemini_api_key="gemini_key"
)

# 티스토리 설정
tistory_writer = TistorySeleniumWriter(
    kakao_email="your_kakao_email@example.com",
    kakao_password="your_password",
    blog_name="mylittleshop"
)

# 티스토리 로그인
tistory_writer.login()

# 멀티 포스팅
manager = MultiBlogManager()
results = manager.post_to_multiple_blogs(
    title="제품 리뷰",
    ai_result=ai_result,
    image_files=image_files,
    shopping_url=shopping_url,
    naver_writer=naver_writer,
    tistory_writer=tistory_writer,
    blog_id="naver_blog_id"
)

# 결과 확인
print(manager.get_summary())

# 정리
tistory_writer.close()
```

---

## 주요 기능

### 1. 자동 로그인
- 카카오 계정으로 로그인
- 쿠키 저장으로 재로그인 불필요
- 쿠키 파일 위치: `%APPDATA%/ColdAPP/tistory_cookies.json`

### 2. HTML 스타일 지원
- inline CSS 완벽 지원
- 박스, 인용구, 색상 등 모든 스타일 적용 가능
- 네이버 블로그와 동일한 형식 사용

### 3. 이미지 업로드
- 로컬 이미지 자동 업로드
- 티스토리 서버에 저장
- HTML에 자동 삽입

### 4. 태그 자동 입력
- 최대 10개 태그 지원
- 엔터키로 구분하여 입력

### 5. 자동 발행
- 글 작성 후 자동 발행
- 발행 URL 반환

---

## 콘텐츠 형식

### 지원하는 태그

```
[TEXT]
일반 텍스트 내용

[QUOTE:UNDERLINE]
소제목 (밑줄 스타일)

[QUOTE:VERTICAL]
강조 박스 (세로 라인)

[IMAGE:1,2,3]
이미지 삽입 (쉼표로 여러 개 가능)

[LINK]
쇼핑 링크 버튼
```

### 예시

```python
ai_result = {
    'content': """
[TEXT] 제품을 사용해본 솔직한 후기입니다.

[QUOTE:UNDERLINE] 제품의 장점

[TEXT] 가성비가 정말 좋아요.

[QUOTE:VERTICAL] 이 제품의 핵심 기능은 바로 이것!

[IMAGE:1]

[TEXT] 사진에서 보시는 것처럼 디자인도 깔끔합니다.

[IMAGE:2,3]

[LINK]
""",
    'tags': ['리뷰', '제품', '추천', '가성비']
}
```

---

## 문제 해결

### 1. 로그인 실패

**증상:** 카카오 로그인이 안 됨

**해결:**
- 카카오 2단계 인증(2FA) 비활성화
- 전용 계정 사용 권장
- 쿠키 파일 삭제 후 재시도: `%APPDATA%/ColdAPP/tistory_cookies.json`

### 2. iframe 오류

**증상:** 본문 입력 안 됨

**해결:**
- 코드에서 자동으로 iframe 전환 처리
- 오류 발생 시 `driver.switch_to.default_content()` 자동 호출

### 3. 이미지 업로드 실패

**증상:** 이미지가 업로드되지 않음

**해결:**
- 이미지 파일 경로가 절대 경로인지 확인
- 파일 크기 확인 (너무 크면 실패 가능)
- 타임아웃 시간 조정

### 4. 발행 버튼 클릭 안 됨

**증상:** 완료 버튼을 찾을 수 없음

**해결:**
- 페이지 로딩 시간 부족 → `time.sleep()` 증가
- 티스토리 UI 변경 → CSS selector 업데이트 필요

---

## 성능 및 제약사항

### 속도
- 로그인: 약 5-10초
- 글 작성: 약 10-20초 (이미지 개수에 따라)
- 총 소요 시간: 약 15-30초

### 제약사항
- 브라우저 창이 보임 (headless 모드 설정 가능)
- 네트워크 속도에 영향 받음
- 티스토리 UI 변경 시 코드 수정 필요

### 안정성
- 쿠키 저장으로 로그인 유지
- 오류 발생 시 자동 복구
- 타임아웃 처리

---

## 파일 구조

```
coldapp찐/
├── modules/
│   ├── blog_writer_tistory.py              # 레거시 (API 종료)
│   ├── blog_writer_tistory_selenium.py     # 신규 (Selenium)
│   ├── multi_blog_manager.py               # 멀티 블로그 관리
│   └── __init__.py
├── test_tistory_selenium.py                # 테스트 스크립트
└── TISTORY_SELENIUM_README.md              # 이 문서
```

---

## 테스트

```bash
# 테스트 스크립트 실행
python test_tistory_selenium.py
```

**주의:** 실행 전 설정 변경 필요
1. `KAKAO_EMAIL` 설정
2. `KAKAO_PASSWORD` 설정
3. `BLOG_NAME` 설정
4. 테스트 이미지 준비

---

## FAQ

### Q1. API 방식보다 느린가요?
**A:** 약간 느립니다 (10-20초 추가). 하지만 API가 종료되어 대안이 없습니다.

### Q2. 계정이 차단될 위험은?
**A:** 전용 계정을 사용하고 과도한 요청을 피하면 안전합니다.

### Q3. headless 모드로 실행 가능한가요?
**A:** 가능합니다. `_init_driver()` 메서드에서 `options.add_argument('--headless')` 주석 해제

### Q4. 여러 티스토리 블로그에 동시 포스팅 가능한가요?
**A:** 각 블로그별로 `TistorySeleniumWriter` 인스턴스를 생성하면 가능합니다.

### Q5. 예약 발행 기능은?
**A:** 현재 즉시 발행만 지원합니다. 향후 추가 예정입니다.

---

## 라이선스

이 프로젝트는 개인/상업적 용도로 자유롭게 사용 가능합니다.

---

## 지원

문제가 발생하면 다음을 확인하세요:
1. Chrome 버전 확인
2. undetected-chromedriver 최신 버전 설치
3. 티스토리 UI 변경 여부 확인
4. 테스트 스크립트로 단계별 디버깅

---

**마지막 업데이트:** 2025-11-05
**버전:** 1.0.0
