"""
멀티 블로그 매니저
- 네이버 블로그 + 티스토리 동시 포스팅
- 한 번의 AI 글 생성으로 여러 블로그에 발행
"""

from typing import Dict, List, Optional
import time


class MultiBlogManager:
    """멀티 블로그 관리 클래스"""

    def __init__(self):
        """초기화"""
        self.results = {
            'naver': None,
            'tistory': None
        }

    def post_to_multiple_blogs(
        self,
        title: str,
        ai_result: Dict,
        image_files: List[str],
        shopping_url: str,
        naver_writer=None,
        tistory_writer=None,
        blog_id: str = None
    ) -> Dict:
        """
        여러 블로그에 동시 포스팅

        Args:
            title: 글 제목
            ai_result: AI 생성 결과 {'content': '...', 'tags': [...]}
            image_files: 이미지 파일 경로 리스트
            shopping_url: 쇼핑 URL
            naver_writer: 네이버 블로그 작성 객체 (선택)
            tistory_writer: 티스토리 블로그 작성 객체 (선택)
            blog_id: 네이버 블로그 ID (naver_writer 사용 시 필수)

        Returns:
            dict: 각 블로그별 포스팅 결과
            {
                'naver': {'success': True/False, 'url': '...', 'error': '...'},
                'tistory': {'success': True/False, 'url': '...', 'error': '...'}
            }
        """
        results = {
            'naver': {'success': False, 'url': None, 'error': None},
            'tistory': {'success': False, 'url': None, 'error': None}
        }

        print("\n" + "=" * 60)
        print("🚀 멀티 블로그 포스팅 시작")
        print("=" * 60)

        # 네이버 블로그 포스팅
        if naver_writer and blog_id:
            print("\n[1/2] 네이버 블로그 포스팅 중...")
            try:
                success = naver_writer.write_and_publish(
                    blog_id=blog_id,
                    title=title,
                    ai_result=ai_result,
                    image_files=image_files,
                    shopping_url=shopping_url
                )

                if success:
                    results['naver']['success'] = True
                    results['naver']['url'] = f"https://blog.naver.com/{blog_id}"
                    print("   ✅ 네이버 블로그 포스팅 성공!")
                else:
                    results['naver']['error'] = "포스팅 실패"
                    print("   ❌ 네이버 블로그 포스팅 실패")

            except Exception as e:
                results['naver']['error'] = str(e)
                print(f"   ❌ 네이버 블로그 오류: {e}")

            time.sleep(2)  # 블로그 간 대기
        else:
            print("\n[1/2] 네이버 블로그 건너뜀 (설정 없음)")

        # 티스토리 포스팅
        if tistory_writer:
            print("\n[2/2] 티스토리 포스팅 중...")
            try:
                result = tistory_writer.write_post(
                    title=title,
                    ai_result=ai_result,
                    image_files=image_files,
                    shopping_url=shopping_url,
                    visibility=3  # 발행
                )

                if result:
                    results['tistory']['success'] = True
                    results['tistory']['url'] = result['tistory']['url']
                    print(f"   ✅ 티스토리 포스팅 성공!")
                    print(f"   URL: {results['tistory']['url']}")
                else:
                    results['tistory']['error'] = "포스팅 실패"
                    print("   ❌ 티스토리 포스팅 실패")

            except Exception as e:
                results['tistory']['error'] = str(e)
                print(f"   ❌ 티스토리 오류: {e}")
        else:
            print("\n[2/2] 티스토리 건너뜀 (설정 없음)")

        # 최종 결과 출력
        print("\n" + "=" * 60)
        print("📊 멀티 블로그 포스팅 결과")
        print("=" * 60)

        success_count = sum(1 for r in results.values() if r['success'])
        total_count = sum(1 for k, r in results.items()
                         if (k == 'naver' and naver_writer) or (k == 'tistory' and tistory_writer))

        print(f"\n✅ 성공: {success_count}/{total_count}")

        if results['naver']['success']:
            print(f"   🟢 네이버: {results['naver']['url']}")
        elif naver_writer:
            print(f"   🔴 네이버: 실패 ({results['naver']['error']})")

        if results['tistory']['success']:
            print(f"   🟢 티스토리: {results['tistory']['url']}")
        elif tistory_writer:
            print(f"   🔴 티스토리: 실패 ({results['tistory']['error']})")

        print("=" * 60 + "\n")

        self.results = results
        return results

    def get_summary(self) -> str:
        """
        포스팅 결과 요약 문자열 생성

        Returns:
            str: 결과 요약
        """
        if not self.results:
            return "포스팅 결과 없음"

        summary_parts = []
        success_count = sum(1 for r in self.results.values() if r['success'])

        if success_count == 0:
            return "❌ 모든 블로그 포스팅 실패"

        summary_parts.append(f"✅ {success_count}개 블로그 포스팅 성공!")

        for blog_name, result in self.results.items():
            if result['success']:
                summary_parts.append(f"  • {blog_name.upper()}: {result['url']}")

        return "\n".join(summary_parts)
