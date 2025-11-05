"""
유틸리티 함수 모듈
- 색상 선택
- 텍스트 처리
- 스타일 관련 헬퍼 함수
"""

import random
import re


class StyleUtils:
    """스타일 관련 유틸리티 클래스"""
    
    @staticmethod
    def get_random_color(color_type='font'):
        """
        랜덤 색상 선택 (네이버 에디터 실제 색상)
        
        Args:
            color_type: 'font' (글자색) 또는 'bg' (배경색)
            
        Returns:
            str: HEX 색상 코드 (예: '#ff5f45')
        """
        if color_type == 'font':
            # 글자색: 진한 색상 위주
            font_colors = [
                '#ff5f45', '#ffa94f', '#ffef34', '#98d36c', '#00b976', '#00bfb5',
                '#00cdff', '#0095e9', '#bc61ab', '#ff65a8', '#ff0010', '#ff9300',
                '#ffd300', '#54b800', '#00a84b', '#009d91', '#00b3f2', '#0078cb',
                '#aa1f91', '#ff008c', '#ba0000', '#b85c00', '#ac9a00', '#36851e',
                '#007433', '#00756a', '#007aa6', '#004e82', '#740060', '#bb005c',
                '#700001', '#823f00', '#6a5f00', '#245b12', '#004e22', '#00554c',
                '#004e6a', '#003960', '#4f0041', '#830041', '#333333', '#555555',
                '#777777', '#999999'
            ]
            return random.choice(font_colors)
        else:
            # 배경색: 연한 색상 위주 (형광펜 효과)
            bg_colors = [
                '#ffcdc0', '#ffe3c8', '#fff8b2', '#e3fdc8', '#c2f4db', '#bdfbfa',
                '#b0f1ff', '#9bdfff', '#fdd5f5', '#ffb7de', '#ffad98', '#ffd1a4',
                '#fff593', '#badf98', '#3fcc9c', '#15d0ca', '#28e1ff', '#5bc7ff',
                '#cd8bc0', '#ff97c1', '#f7f7f7', '#e2e2e2', '#c2c2c2', '#ffffff'
            ]
            return random.choice(bg_colors)
    
    @staticmethod
    def soft_avoid_phrases(text):
        """
        상투적인 문구를 동의어로 치환하여 자연스럽게 만들기
        
        Args:
            text: 원본 텍스트
            
        Returns:
            str: 처리된 텍스트
        """
        groups = [
            {
                'targets': [
                    '안녕하세요!', '안녕하세요.', '안녕하세요',
                    '요즘 필요한 제품을 찾다가', '여러 제품을 비교해본 결과'
                ],
                'alts': ['첫 느낌부터', '처음 보고 느낀 건', '필요가 생겨 제품을 찾아보던 중', '사용 배경부터']
            },
            {
                'targets': ['정말 만족스러웠어요', '만족스러웠어요', '정말 만족스럽습니다'],
                'alts': ['쓸 만했습니다', '기대치엔 부합했습니다', '체감 성능은 무난했습니다']
            },
            {
                'targets': ['가성비가 좋아요', '가격 대비 이 정도면 충분해요', '가격 대비 괜찮아요'],
                'alts': ['가격 대비 포지션은 명확합니다', '동급 대비 조건은 나쁘지 않습니다', '예산 대비 선택지는 됩니다']
            },
            {
                'targets': ['추천드립니다', '추천합니다', '강추합니다'],
                'alts': ['선택지로 고려해볼 만합니다', '이런 용도라면 맞을 수 있습니다', '상황에 따라 유효한 대안이 됩니다']
            },
            {
                'targets': ['물론 완벽한 제품은 없듯이', '아쉬운 부분도 있었어요'],
                'alts': ['완벽하진 않아서', '쓰다 보니 보완할 지점도 있습니다']
            }
        ]
        
        for group in groups:
            pattern = re.compile('|'.join(re.escape(t) for t in group['targets']))
            cnt = {'n': 0}
            
            def repl(m):
                cnt['n'] += 1
                if cnt['n'] == 1:
                    # 첫 등장은 50% 확률로 유지
                    return m.group(0) if random.random() < 0.5 else random.choice(group['alts'])
                return random.choice(group['alts'])
            
            text = pattern.sub(repl, text)
        
        return text
    
    @staticmethod
    def remove_markdown(text):
        """
        마크다운 기호 제거
        
        Args:
            text: 마크다운 텍스트
            
        Returns:
            str: 일반 텍스트
        """
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        return text
