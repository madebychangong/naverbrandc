"""
콘텐츠 히스토리 관리 모듈
- 작성된 글의 메타데이터 저장
- 카테고리별 접근 각도 분석
- 차별화 전략 제안
- 다중 프로세스 지원 (파일 잠금 처리)
"""

import os
import json
from datetime import datetime
import re
import time


class ContentHistoryManager:
    """콘텐츠 히스토리 관리 클래스"""

    # 카테고리 키워드 매핑
    CATEGORY_KEYWORDS = {
        '이불': ['이불', '침구', '베개', '담요', '쿠션', '매트리스', '패드'],
        '멀티탭': ['멀티탭', '콘센트', '전선', '파워', '어댑터'],
        '정수기': ['정수기', '필터', '정수', '생수', '물'],
        '가전제품': ['세탁기', '냉장고', '에어컨', '청소기', '건조기', '공기청정기'],
        '주방용품': ['냄비', '프라이팬', '그릇', '칼', '도마', '주방'],
        '가구': ['책상', '의자', '침대', '소파', '수납장', '선반'],
        '화장품': ['스킨', '로션', '크림', '에센스', '마스크팩', '화장품'],
        '식품': ['과자', '음료', '건강식품', '영양제', '커피', '차'],
        '의류': ['옷', '바지', '셔츠', '티셔츠', '자켓', '코트'],
        '신발': ['신발', '운동화', '슬리퍼', '샌들', '구두'],
        '전자기기': ['스마트폰', '노트북', '태블릿', '이어폰', '마우스', '키보드'],
        '생활용품': ['휴지', '세제', '샴푸', '비누', '치약', '칫솔']
    }

    # 접근 각도별 키워드
    APPROACH_KEYWORDS = {
        '소재/촉감': ['소재', '촉감', '재질', '원단', '질감', '부드러운', '거친', '매끄러운'],
        '크기/용량': ['크기', '용량', '치수', '사이즈', '넓은', '큰', '작은', 'L', 'ml', 'cm'],
        '기능/성능': ['기능', '성능', '속도', '효율', '파워', '작동', '자동'],
        '디자인/색상': ['디자인', '색상', '색깔', '예쁜', '멋진', '스타일', '모던', '깔끔'],
        '가성비/가격': ['가격', '가성비', '저렴', '합리적', '경제적', '만원', '원'],
        '편의성/관리': ['편리', '관리', '세탁', '청소', '간편', '쉬운', '보관'],
        '안전성': ['안전', '인증', '보증', '무해', '친환경', '검증'],
        '사용감/경험': ['사용', '경험', '느낌', '만족', '실제', '후기']
    }

    def __init__(self, history_dir=None):
        """
        초기화

        Args:
            history_dir: 히스토리 저장 디렉토리 (None이면 기본 경로 사용)
        """
        if history_dir is None:
            # AppData/Roaming/ColdAPP/content_history.json
            app_data = os.getenv("APPDATA")
            self.history_dir = os.path.join(app_data, "ColdAPP")
        else:
            self.history_dir = history_dir

        self.history_file = os.path.join(self.history_dir, "content_history.json")

        # 디렉토리 생성
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir, exist_ok=True)

    def classify_category(self, product_title):
        """
        제품명으로부터 카테고리 자동 분류

        Args:
            product_title: 제품명

        Returns:
            str: 카테고리명
        """
        title_lower = product_title.lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category

        # 매칭 안 되면 '기타'
        return '기타'

    def detect_approach_angle(self, content):
        """
        작성된 글 내용으로부터 접근 각도 자동 감지

        Args:
            content: 작성된 글 내용

        Returns:
            list: 감지된 접근 각도 리스트 (최대 3개)
        """
        if not content:
            return []

        content_lower = content.lower()
        approach_scores = {}

        for approach, keywords in self.APPROACH_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # 키워드 출현 횟수 계산
                score += content_lower.count(keyword)
            approach_scores[approach] = score

        # 점수 높은 순으로 정렬하여 상위 3개 반환
        sorted_approaches = sorted(approach_scores.items(), key=lambda x: x[1], reverse=True)
        detected_approaches = [approach for approach, score in sorted_approaches[:3] if score > 0]

        return detected_approaches

    def extract_key_points(self, content):
        """
        작성된 글에서 주요 키워드 추출

        Args:
            content: 작성된 글 내용

        Returns:
            list: 주요 키워드 리스트 (최대 5개)
        """
        if not content:
            return []

        # 간단한 키워드 추출 (명사구 위주)
        # [QUOTE:UNDERLINE] 섹션의 제목들 추출
        quote_pattern = r'\[QUOTE:UNDERLINE\]\s*([^\[]+)'
        quotes = re.findall(quote_pattern, content)

        key_points = []
        for quote in quotes[:5]:
            cleaned = quote.strip().replace('\n', ' ')
            if cleaned and len(cleaned) > 2:
                key_points.append(cleaned[:30])  # 최대 30자

        return key_points

    def save_history(self, product_title, content, approach_angle=None):
        """
        글 작성 히스토리 저장 (파일 잠금 처리)

        Args:
            product_title: 제품명
            content: 작성된 글 내용
            approach_angle: 사용된 접근 각도 (None이면 자동 감지)
        """
        max_retries = 5
        retry_delay = 0.5  # 0.5초

        for attempt in range(max_retries):
            try:
                # 기존 히스토리 로드 (재시도 포함)
                history = self.load_history()

                # 카테고리 자동 분류
                category = self.classify_category(product_title)

                # 접근 각도 감지 (제공되지 않은 경우)
                if approach_angle is None:
                    detected_approaches = self.detect_approach_angle(content)
                    approach_angle = detected_approaches[0] if detected_approaches else "일반"

                # 주요 키워드 추출
                key_points = self.extract_key_points(content)

                # 새 항목 추가
                new_entry = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'product_title': product_title[:100],  # 최대 100자
                    'category': category,
                    'approach_angle': approach_angle,
                    'key_points': key_points
                }

                history['entries'].append(new_entry)

                # 최대 50개만 유지 (오래된 것부터 삭제)
                if len(history['entries']) > 50:
                    history['entries'] = history['entries'][-50:]

                # 파일 잠금과 함께 저장
                import msvcrt
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    # 파일 잠금 시도
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                        json.dump(history, f, indent=2, ensure_ascii=False)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                        print(f"   ✅ 히스토리 저장: {category} - {approach_angle}")
                        return
                    except IOError:
                        # 파일이 잠겨있으면 재시도
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"   ⚠️ 히스토리 저장 실패 (무시): {e}")

    def load_history(self):
        """
        히스토리 로드 (파일 잠금 처리)

        Returns:
            dict: 히스토리 데이터
        """
        if not os.path.exists(self.history_file):
            return {'entries': []}

        max_retries = 5
        retry_delay = 0.3  # 0.3초

        for attempt in range(max_retries):
            try:
                import msvcrt
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    try:
                        # 공유 잠금 (읽기 전용)
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                        data = json.load(f)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                        return data
                    except IOError:
                        # 파일이 잠겨있으면 재시도
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            # 최종 실패 시 잠금 없이 읽기 시도
                            f.seek(0)
                            return json.load(f)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"   ⚠️ 히스토리 로드 실패: {e}")
                    return {'entries': []}

    def get_recent_by_category(self, category, limit=5):
        """
        특정 카테고리의 최근 글 조회

        Args:
            category: 카테고리명
            limit: 조회할 개수

        Returns:
            list: 최근 글 리스트
        """
        history = self.load_history()
        entries = history.get('entries', [])

        # 해당 카테고리 필터링
        category_entries = [e for e in entries if e.get('category') == category]

        # 최신순으로 정렬하여 limit 개수만 반환
        return category_entries[-limit:]

    def suggest_differentiation_strategy(self, product_title, current_approach=None):
        """
        차별화 전략 제안

        Args:
            product_title: 현재 제품명
            current_approach: 현재 사용 중인 접근 각도 (있다면)

        Returns:
            dict: {
                'category': 카테고리,
                'recent_approaches': 최근 사용된 접근 각도 리스트,
                'suggested_approaches': 추천 접근 각도 리스트,
                'differentiation_tip': 차별화 팁
            }
        """
        # 카테고리 분류
        category = self.classify_category(product_title)

        # 최근 5개 글 조회
        recent_entries = self.get_recent_by_category(category, limit=5)

        # 최근 사용된 접근 각도 추출
        recent_approaches = []
        for entry in recent_entries:
            approach = entry.get('approach_angle')
            if approach and approach not in recent_approaches:
                recent_approaches.append(approach)

        # 모든 가능한 접근 각도
        all_approaches = list(self.APPROACH_KEYWORDS.keys())

        # 아직 사용되지 않은 접근 각도 우선 추천
        unused_approaches = [a for a in all_approaches if a not in recent_approaches]

        # 추천 접근 각도 (미사용 우선, 없으면 전체에서)
        if unused_approaches:
            suggested_approaches = unused_approaches[:3]
        else:
            # 모두 사용했으면 가장 오래 사용 안 된 것 추천
            suggested_approaches = all_approaches[:3]

        # 차별화 팁 생성
        differentiation_tip = ""
        if len(recent_entries) > 0:
            recent_count = len(recent_entries)
            differentiation_tip = f"최근 {recent_count}개의 {category} 리뷰에서 {', '.join(recent_approaches[:2])} 위주로 작성되었습니다. "
            differentiation_tip += f"이번에는 {suggested_approaches[0]}을 중심으로 작성하면 차별화됩니다."
        else:
            differentiation_tip = f"{category} 카테고리 첫 리뷰입니다. {suggested_approaches[0]}을 중심으로 작성하세요."

        return {
            'category': category,
            'recent_approaches': recent_approaches,
            'suggested_approaches': suggested_approaches,
            'differentiation_tip': differentiation_tip,
            'recent_count': len(recent_entries)
        }
