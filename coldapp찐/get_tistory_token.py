"""
티스토리 Access Token 발급 도구
- 티스토리 OpenAPI 앱 등록 후 사용
- OAuth 2.0 인증 플로우 자동화
"""

import webbrowser
import requests
import sys


def get_tistory_access_token():
    """티스토리 Access Token 발급"""

    print("=" * 60)
    print("티스토리 Access Token 발급 도구")
    print("=" * 60)
    print()

    # 1. 앱 정보 입력
    print("📌 티스토리 OpenAPI 앱 등록:")
    print("   https://www.tistory.com/guide/api/manage/list")
    print()

    app_id = input("App ID를 입력하세요: ").strip()
    if not app_id:
        print("❌ App ID가 필요합니다.")
        return

    secret_key = input("Secret Key를 입력하세요: ").strip()
    if not secret_key:
        print("❌ Secret Key가 필요합니다.")
        return

    redirect_uri = "http://localhost/callback"

    print()
    print("=" * 60)

    # 2. 인증 URL 생성
    auth_url = (
        f"https://www.tistory.com/oauth/authorize?"
        f"client_id={app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&state=coldapp"
    )

    print("🔐 Step 1: 브라우저에서 인증")
    print("=" * 60)
    print()
    print("브라우저가 자동으로 열립니다.")
    print("티스토리에 로그인하고 권한을 승인하세요.")
    print()
    print("만약 브라우저가 열리지 않으면 아래 URL을 복사해서 접속하세요:")
    print(auth_url)
    print()

    input("준비되면 Enter를 누르세요...")

    # 브라우저 열기
    webbrowser.open(auth_url)

    print()
    print("=" * 60)
    print("🔐 Step 2: Authorization Code 입력")
    print("=" * 60)
    print()
    print("브라우저가 리다이렉트되면 주소창의 URL을 확인하세요.")
    print("예: http://localhost/callback?code=abc123xyz&state=coldapp")
    print()
    print("URL에서 'code=' 뒤의 값을 복사하세요.")
    print("(예: abc123xyz)")
    print()

    code = input("Authorization Code를 입력하세요: ").strip()
    if not code:
        print("❌ Authorization Code가 필요합니다.")
        return

    print()
    print("=" * 60)
    print("🔐 Step 3: Access Token 발급 중...")
    print("=" * 60)
    print()

    # 3. Access Token 요청
    try:
        token_url = "https://www.tistory.com/oauth/access_token"

        params = {
            "client_id": app_id,
            "client_secret": secret_key,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code"
        }

        response = requests.get(token_url, params=params, timeout=10)

        print(f"API 응답: {response.text}")
        print()

        if "access_token=" in response.text:
            token = response.text.split("=")[1]

            print("=" * 60)
            print("✅ Access Token 발급 성공!")
            print("=" * 60)
            print()
            print(f"Access Token: {token}")
            print()
            print("=" * 60)
            print("📝 다음 단계:")
            print("=" * 60)
            print()
            print("1. ColdAPP 실행")
            print("2. [설정] 탭 이동")
            print("3. [📘 티스토리 (선택)] 섹션에서:")
            print(f"   - 블로그 이름: (예: myblog)")
            print(f"   - Access Token: {token}")
            print("4. [설정 저장] 클릭")
            print()
            print("🎉 이제 네이버 + 티스토리 동시 포스팅이 가능합니다!")
            print()

        else:
            print("=" * 60)
            print("❌ Access Token 발급 실패")
            print("=" * 60)
            print()
            print("오류 원인:")
            print("1. App ID 또는 Secret Key가 잘못되었습니다")
            print("2. Authorization Code가 만료되었습니다 (1시간 제한)")
            print("3. Callback URL이 일치하지 않습니다")
            print()
            print("다시 시도해주세요.")
            print()

    except requests.exceptions.RequestException as e:
        print("=" * 60)
        print("❌ 네트워크 오류")
        print("=" * 60)
        print()
        print(f"오류: {e}")
        print()
        print("인터넷 연결을 확인하고 다시 시도하세요.")
        print()

    except Exception as e:
        print("=" * 60)
        print("❌ 예상치 못한 오류")
        print("=" * 60)
        print()
        print(f"오류: {e}")
        print()


if __name__ == "__main__":
    try:
        get_tistory_access_token()
    except KeyboardInterrupt:
        print("\n\n사용자가 취소했습니다.")
        sys.exit(0)

    print()
    input("종료하려면 Enter를 누르세요...")
