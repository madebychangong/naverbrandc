# 티스토리 멀티 블로그 포스팅 가이드 📘

ColdAPP에 티스토리 자동 포스팅 기능이 추가되었습니다!
**한 번의 클릭으로 네이버 블로그와 티스토리에 동시 포스팅**할 수 있습니다.

---

## 🎯 주요 기능

- ✅ **AI 글 생성은 1번만** - 비용 절감!
- ✅ **네이버 + 티스토리 동시 포스팅** - 도달률 2배
- ✅ **자동 이미지 업로드** - 티스토리 API 활용
- ✅ **HTML 자동 변환** - 네이버 형식 → 티스토리 HTML

---

## ⚙️ 티스토리 설정 방법

### 1단계: 티스토리 OpenAPI 앱 등록

1. **티스토리 OpenAPI 사이트 접속**
   - https://www.tistory.com/guide/api/manage/list

2. **앱 등록하기 클릭**
   - 서비스명: ColdAPP (또는 원하는 이름)
   - 서비스 URL: http://localhost
   - Callback: http://localhost/callback

3. **App ID와 Secret Key 발급받기**
   - 앱 등록 후 App ID와 Secret Key를 확인합니다

### 2단계: Access Token 발급

티스토리는 OAuth 2.0 방식으로 Access Token을 발급합니다.

**방법 1: 간단한 방법 (브라우저 사용)**

1. 아래 URL에서 `{APP_ID}`를 발급받은 App ID로 변경:
```
https://www.tistory.com/oauth/authorize?client_id={APP_ID}&redirect_uri=http://localhost/callback&response_type=code
```

2. 브라우저에서 위 URL 접속
3. 로그인 후 권한 승인
4. 리다이렉트된 URL에서 `code` 파라미터 복사
   - 예: `http://localhost/callback?code=abc123xyz` → `abc123xyz` 복사

5. 아래 URL에서 필요한 정보 변경 후 브라우저 접속:
```
https://www.tistory.com/oauth/access_token?client_id={APP_ID}&client_secret={SECRET_KEY}&redirect_uri=http://localhost/callback&code={CODE}&grant_type=authorization_code
```

6. 화면에 표시된 `access_token=xxx` 부분의 `xxx`를 복사

**방법 2: Python 스크립트 사용**

`coldapp찐` 폴더에 `get_tistory_token.py` 파일을 만들고:

```python
import webbrowser
import requests

# 발급받은 정보 입력
APP_ID = "your_app_id_here"
SECRET_KEY = "your_secret_key_here"
REDIRECT_URI = "http://localhost/callback"

# 1단계: 인증 URL 생성 및 열기
auth_url = (
    f"https://www.tistory.com/oauth/authorize?"
    f"client_id={APP_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code"
)

print("브라우저에서 로그인하고 권한을 승인하세요...")
print(f"URL: {auth_url}")
webbrowser.open(auth_url)

# 2단계: Authorization Code 입력
code = input("\n리다이렉트된 URL의 code 파라미터를 입력하세요: ").strip()

# 3단계: Access Token 발급
token_url = "https://www.tistory.com/oauth/access_token"
params = {
    "client_id": APP_ID,
    "client_secret": SECRET_KEY,
    "redirect_uri": REDIRECT_URI,
    "code": code,
    "grant_type": "authorization_code"
}

response = requests.get(token_url, params=params)
print(f"\n응답: {response.text}")

if "access_token=" in response.text:
    token = response.text.split("=")[1]
    print(f"\n✅ Access Token 발급 성공!")
    print(f"Token: {token}")
    print(f"\n이 토큰을 ColdAPP 설정에 입력하세요.")
else:
    print("❌ 토큰 발급 실패")
```

실행:
```bash
python get_tistory_token.py
```

### 3단계: 블로그 이름 확인

티스토리 블로그 주소가 `https://myblog.tistory.com`이라면,
블로그 이름은 `myblog`입니다.

### 4단계: ColdAPP 설정

1. ColdAPP 실행
2. **설정** 탭 이동
3. **📘 티스토리 (선택)** 섹션에 입력:
   - **블로그 이름**: `myblog`
   - **Access Token**: `발급받은 토큰`
4. **✅ 포스팅할 블로그 선택**에서 **티스토리** 체크
5. **설정 저장** 클릭

---

## 🚀 사용 방법

### 1. 네이버 + 티스토리 동시 포스팅

1. **설정** 탭에서:
   - ✅ 네이버 블로그 체크
   - ✅ 티스토리 체크

2. **자동 포스팅** 탭에서:
   - 쇼핑 URL 입력
   - **시작하기** 클릭

3. 결과:
   - 🟢 네이버 블로그 포스팅 완료
   - 🟢 티스토리 포스팅 완료

### 2. 네이버만 포스팅

- ✅ 네이버 블로그만 체크
- ❌ 티스토리 체크 해제

### 3. 티스토리만 포스팅

**현재 지원하지 않습니다.**
네이버 브라우저를 통해 상품 정보를 수집하므로, 네이버는 필수입니다.

---

## 📊 작동 원리

```
쇼핑 URL 입력
    ↓
[네이버 브라우저로 상품 정보 수집]
    ├─ 상품명, 가격, 설명
    ├─ 대표 이미지 다운로드
    └─ 상세 이미지 다운로드
    ↓
[AI 글 생성 - 1번만!]
    ├─ Gemini Vision API로 이미지 분석
    └─ 네이버 형식 콘텐츠 생성
    ↓
[멀티 블로그 포스팅]
    ├─ 네이버: Selenium으로 직접 작성
    └─ 티스토리: REST API로 HTML 변환 후 전송
```

---

## 🎨 네이버 형식 → 티스토리 변환

ColdAPP는 네이버 블로그 형식을 자동으로 티스토리 HTML로 변환합니다:

| 네이버 형식 | 티스토리 HTML |
|------------|--------------|
| `[TEXT]` | `<p>` 태그 |
| `[QUOTE:VERTICAL]` | 배경색 박스 |
| `[QUOTE:UNDERLINE]` | `<h3>` 제목 |
| `[IMAGE:1,2]` | `<img>` 태그 |
| `[LINK]` | 버튼 스타일 링크 |

---

## ⚠️ 주의사항

### 1. 티스토리 OpenAPI 종료 예정

티스토리 OpenAPI는 **단계적으로 종료** 예정입니다:
- 공지: https://notice.tistory.com/2664
- 종료 순서: 파일 첨부 → 글 작성 → 댓글
- **현재는 사용 가능**하지만, 향후 종료 시 Selenium 방식으로 전환 예정

### 2. Access Token 관리

- Access Token은 **외부에 노출되지 않도록** 주의하세요
- 만료되면 재발급 필요 (재발급 절차는 동일)

### 3. Rate Limiting

- 티스토리 API는 공식 Rate Limit이 없지만, **1-2초 간격**으로 요청합니다
- 이미지 업로드는 개별적으로 진행되므로 시간이 걸릴 수 있습니다

### 4. 이미지 업로드

- 티스토리는 **이미지당 최대 10MB** 제한
- 자동으로 HTTPS URL로 변환됩니다

---

## 🔍 문제 해결

### "티스토리 연결 실패"

1. Access Token이 올바른지 확인
2. 블로그 이름이 정확한지 확인 (myblog.tistory.com → `myblog`)
3. 네트워크 연결 확인

### "이미지 업로드 실패"

1. 이미지 파일 크기 확인 (10MB 이하)
2. 이미지 형식 확인 (JPG, PNG 권장)
3. 티스토리 API 상태 확인

### "HTML 변환 오류"

- 로그 확인 (진행 상황 창)
- GitHub Issue에 오류 내용 제보

---

## 📝 예제

### 전체 과정 예시

```
1. 티스토리 앱 등록
   → App ID: 12345
   → Secret: abc...xyz

2. Access Token 발급
   → Token: def...ghi

3. ColdAPP 설정
   → 블로그 이름: mytech
   → Access Token: def...ghi
   → 네이버 + 티스토리 모두 체크

4. 포스팅 실행
   → URL: https://naver.me/xxxxx
   → 시작하기 클릭

5. 결과
   ✅ 네이버: https://blog.naver.com/myid/123
   ✅ 티스토리: https://mytech.tistory.com/456
```

---

## 💡 팁

### 1. 비용 절감

- AI 글은 1번만 생성되므로 **Gemini API 비용이 2배가 되지 않습니다**
- 네이버만 사용: 약 13원/글
- 네이버 + 티스토리: 약 13원/글 (동일!)

### 2. 도달률 증가

- 네이버 블로그: 네이버 검색 노출
- 티스토리: 다음(Daum) 검색 노출
- **두 플랫폼 동시 활용으로 유입 경로 다양화**

### 3. 백업 효과

- 한 플랫폼에 문제가 생겨도 다른 플랫폼에 콘텐츠 보존

---

## 🎉 완성!

이제 ColdAPP로 **네이버 블로그와 티스토리에 동시에 자동 포스팅**할 수 있습니다!

궁금한 점이 있으면 GitHub Issue를 남겨주세요.

**Made by Changong** 💙
