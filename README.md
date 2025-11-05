# naverbrandc

## 티스토리 로그인 및 포스팅 테스트

티스토리 자동 로그인 및 포스팅 기능을 테스트하는 스크립트입니다.

### 설치

```bash
pip install -r requirements.txt
```

### 사용법

1. `tistory_login_posting_test.py` 파일을 열어 설정 값을 입력합니다:
   - `BLOG_NAME`: 티스토리 블로그 이름 (예: myblog)
   - `EMAIL`: 카카오 계정 이메일
   - `PASSWORD`: 카카오 계정 비밀번호

2. 스크립트 실행:
```bash
python tistory_login_posting_test.py
```

### 기능

- 카카오 계정으로 티스토리 로그인
- 로그인 후 자동으로 글쓰기 페이지 이동
- 제목과 내용에 "테스트" 입력
- 포스팅 자동 발행

### 주의사항

- Chrome 브라우저가 설치되어 있어야 합니다
- 로그인 정보를 정확히 입력해주세요
- 에러 발생 시 `error_screenshot.png` 파일이 생성됩니다