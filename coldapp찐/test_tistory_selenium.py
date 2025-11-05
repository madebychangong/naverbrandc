"""
티스토리 Selenium 자동 포스팅 테스트 스크립트
"""

from modules.blog_writer_tistory_selenium import TistorySeleniumWriter

# 테스트 설정
KAKAO_EMAIL = "your_kakao_email@example.com"
KAKAO_PASSWORD = "your_password"
BLOG_NAME = "mylittleshop"  # 티스토리 블로그 이름


def test_tistory_posting():
    """티스토리 Selenium 포스팅 테스트"""

    print("=" * 60)
    print("🧪 티스토리 Selenium 자동 포스팅 테스트")
    print("=" * 60)

    # 1. TistorySeleniumWriter 초기화
    writer = TistorySeleniumWriter(
        kakao_email=KAKAO_EMAIL,
        kakao_password=KAKAO_PASSWORD,
        blog_name=BLOG_NAME
    )

    try:
        # 2. 로그인
        if not writer.login():
            print("❌ 로그인 실패")
            return False

        # 3. 테스트 데이터 준비 (제목과 내용에 "테스트"만 입력)
        title = "테스트"

        ai_result = {
            'content': """[TEXT] 테스트""",
            'tags': ['테스트']
        }

        # 이미지 없이 테스트
        image_files = []

        shopping_url = "https://example.com"

        # 4. 글 작성
        success = writer.write_post(
            title=title,
            ai_result=ai_result,
            image_files=image_files,
            shopping_url=shopping_url
        )

        if success:
            print("\n" + "=" * 60)
            print("✅ 테스트 성공!")
            print(f"   블로그: https://{BLOG_NAME}.tistory.com")
            print("=" * 60)
            return True
        else:
            print("\n❌ 테스트 실패")
            return False

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 5. 브라우저 종료
        writer.close()


def test_multi_blog():
    """네이버 + 티스토리 멀티 블로그 포스팅 테스트"""
    from modules.multi_blog_manager import MultiBlogManager
    from naver_blog_automation import NaverBlogAutomation

    print("=" * 60)
    print("🧪 멀티 블로그 포스팅 테스트")
    print("=" * 60)

    # 네이버 블로그 설정
    naver_writer = NaverBlogAutomation(
        blog_id="your_naver_blog_id",
        naver_id="your_naver_id",
        naver_pw="your_naver_pw",
        gemini_api_key="your_gemini_key"
    )

    # 티스토리 설정
    tistory_writer = TistorySeleniumWriter(
        kakao_email=KAKAO_EMAIL,
        kakao_password=KAKAO_PASSWORD,
        blog_name=BLOG_NAME
    )

    # 티스토리 로그인
    if not tistory_writer.login():
        print("❌ 티스토리 로그인 실패")
        return False

    # 멀티 블로그 매니저
    manager = MultiBlogManager()

    # 테스트 데이터
    title = "멀티 블로그 테스트 - 네이버 + 티스토리"
    ai_result = {
        'content': """
[TEXT] 네이버와 티스토리에 동시 포스팅 테스트입니다.

[QUOTE:UNDERLINE] 멀티 블로그 포스팅

[TEXT] 한 번의 실행으로 여러 블로그에 글을 발행합니다.

[IMAGE:1]

[LINK]
""",
        'tags': ['멀티블로그', '자동화', '네이버', '티스토리']
    }

    image_files = ["temp_images/test_image.jpg"]
    shopping_url = "https://example.com"

    # 멀티 포스팅 실행
    results = manager.post_to_multiple_blogs(
        title=title,
        ai_result=ai_result,
        image_files=image_files,
        shopping_url=shopping_url,
        naver_writer=naver_writer,
        tistory_writer=tistory_writer,
        blog_id="your_naver_blog_id"
    )

    # 결과 출력
    print("\n" + manager.get_summary())

    # 정리
    tistory_writer.close()

    return results['naver']['success'] or results['tistory']['success']


if __name__ == "__main__":
    # 개별 티스토리 테스트 (로그인 후 바로 "테스트" 포스팅)
    test_tistory_posting()

    # 멀티 블로그 테스트
    # test_multi_blog()

    # print("\n⚠️ 사용 전 설정을 변경하세요:")
    # print("   1. KAKAO_EMAIL, KAKAO_PASSWORD 입력")
    # print("   2. BLOG_NAME 설정")
    # print("   3. 테스트 이미지 경로 확인")
    # print("   4. test_tistory_posting() 주석 해제")
