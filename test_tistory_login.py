"""
티스토리 로그인 단독 테스트
- 문제 진단용
- 각 단계마다 상세 로그 출력
"""

import sys
import time
from modules.blog_writer_tistory_selenium import TistorySeleniumWriter

def test_tistory_login():
    """티스토리 로그인 테스트"""

    # 사용자 입력
    print("="*60)
    print("🧪 티스토리 로그인 테스트")
    print("="*60)

    kakao_email = input("\n📧 카카오 이메일: ").strip()
    kakao_password = input("🔒 카카오 비밀번호: ").strip()
    blog_name = input("📝 티스토리 블로그 이름 (예: myblog): ").strip()

    if not kakao_email or not kakao_password or not blog_name:
        print("❌ 모든 정보를 입력해주세요!")
        return

    print("\n" + "="*60)
    print("🚀 로그인 시작...")
    print("="*60)

    try:
        # TistorySeleniumWriter 생성
        writer = TistorySeleniumWriter(
            kakao_email=kakao_email,
            kakao_password=kakao_password,
            blog_name=blog_name
        )

        # 로그인 시도
        print("\n📍 login() 메서드 호출 중...\n")
        success = writer.login()

        print("\n" + "="*60)
        if success:
            print("✅ 로그인 성공!")
            print(f"   현재 URL: {writer.driver.current_url}")
            print(f"   is_logged_in: {writer.is_logged_in}")

            # 10초 대기 (화면 확인용)
            print("\n⏳ 10초 대기 중 (브라우저 확인)...")
            time.sleep(10)

        else:
            print("❌ 로그인 실패!")
            print(f"   현재 URL: {writer.driver.current_url}")
            print(f"   is_logged_in: {writer.is_logged_in}")

            # 10초 대기 (문제 확인용)
            print("\n⏳ 10초 대기 중 (화면 확인)...")
            time.sleep(10)

        print("="*60)

        # 브라우저 종료
        input("\n👉 Enter 키를 누르면 브라우저가 종료됩니다...")
        writer.driver.quit()

    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_tistory_login()
