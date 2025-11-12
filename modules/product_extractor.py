"""
상품 정보 추출 모듈
- 상품명, 가격, 설명 추출
- 상품 대표 이미지 추출
- 상세 설명 이미지 추출 (Vision API용) ⭐ 신규
"""

import time
import re
from selenium.webdriver.common.by import By


class ProductExtractor:
    """상품 정보 추출 클래스"""
    
    def __init__(self, driver):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver 객체
        """
        self.driver = driver
    
    def extract_product_info(self, shopping_url):
        """
        쇼핑 URL에서 제품 정보 추출
        
        Args:
            shopping_url: 네이버 쇼핑 URL
            
        Returns:
            dict: {
                'title': 상품명,
                'price': 가격,
                'description': 텍스트 설명,
                'images': 대표 이미지 URL 리스트,
                'link': 원본 URL
            }
        """
        print(f"\n📦 제품 정보 추출 중...")
        print(f"   URL: {shopping_url}")
        
        try:
            # URL 접근
            if 'naver.me' in shopping_url:
                print("   🔄 짧은 URL 리다이렉트 확인...")
                self.driver.get(shopping_url)
                time.sleep(3)
                final_url = self.driver.current_url
                print(f"   ✅ 리다이렉트: {final_url}")
                time.sleep(3)
            else:
                print(f"   🔄 URL 접근 중...")
                self.driver.get(shopping_url)
                time.sleep(5)
                print(f"   ✅ 페이지 로드 완료")
            
            # 제품 정보 추출
            title = self._extract_title()
            price = self._extract_price()
            description = self._extract_description()
            images = self._extract_images()
            
            print(f"\n✅ 제품 정보 추출 완료:")
            print(f"   - 제품명: {title[:50]}...")
            print(f"   - 가격: {price}")
            print(f"   - 텍스트 설명: {len(description)}자")
            print(f"   - 대표 이미지: {len(images)}개")
            
            return {
                'title': title,
                'price': price,
                'description': description,
                'images': images,
                'link': shopping_url
            }
            
        except Exception as e:
            print(f"❌ 제품 정보 추출 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_title(self):
        """제품명 추출"""
        selectors = [
            'h3.YbkZ4Jg2_z',
            'h3.DCVBehA8ZB',
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    title = element.text.strip()
                    if title and len(title) > 3:
                        # [히든딜], [커넥트 히든딜] 등 대괄호 패턴 제거
                        title = re.sub(r'^\[.*?\]\s*', '', title)
                        return title
            except:
                continue
        
        return "제품명을 찾을 수 없습니다"
    
    def _extract_price(self):
        """가격 추출"""
        selectors = [
            'span.xMK43',
            'span._1LY7DqCnwR',
            '.price',
            '[class*="price"]'
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    price = element.text.strip()
                    if price and ('원' in price or ',' in price):
                        return price
            except:
                continue
        
        return "가격 정보 없음"
    
    def _extract_description(self):
        """제품 설명 추출 (텍스트만)"""
        exclude_keywords = ['상품정보 제공고시', '배송', '반품', '교환', '문의', '결제', '주문']
        
        selectors = [
            'div.se-main-container',
            'div.se-viewer',
            'div.nKuwJ',
            'div._3cWR_0Clkt',
        ]
        
        description_parts = []
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 10:
                        # 제외 키워드 필터링
                        if not any(keyword in text for keyword in exclude_keywords):
                            description_parts.append(text)
                            if len(' '.join(description_parts)) > 500:
                                break
            except:
                continue
            
            if len(' '.join(description_parts)) > 500:
                break
        
        if description_parts:
            return ' '.join(description_parts)[:500]
        
        return "제품 설명을 찾을 수 없습니다"
    
    def _extract_images(self):
        """
        상품 대표 이미지 URL 추출 (썸네일 클릭 방식)
        블로그에 올릴 메인 이미지들
        """
        print("   📸 대표 이미지 수집 중...")
        image_urls = []
        
        try:
            # 썸네일 리스트 찾기
            thumbnail_selector = 'li.AIvsO_QzbN a'
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, thumbnail_selector)
            
            print(f"   🔍 썸네일 {len(thumbnails)}개 발견")
            
            if len(thumbnails) > 0:
                # 썸네일 클릭해서 고화질 이미지 가져오기
                for idx, thumbnail in enumerate(thumbnails[:6]):  # 최대 6개
                    try:
                        thumbnail.click()
                        time.sleep(0.8)
                        
                        # 메인 이미지 찾기
                        selectors = [
                            'img.TgO1N1wWTm[alt="대표이미지"]',
                            'img.TgO1N1wWTm',
                            'div._2LuLme7XCi img',
                            'div.image_viewer img',
                            'img[alt="대표이미지"]',
                        ]
                        
                        main_img = None
                        for selector in selectors:
                            try:
                                main_img = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if main_img and main_img.get_attribute('src'):
                                    break
                            except:
                                continue
                        
                        if not main_img:
                            continue
                        
                        src = main_img.get_attribute('src')
                        if not src:
                            continue
                        
                        # 고화질 변환
                        if '?type=' in src:
                            src = src.split('?type=')[0] + '?type=f640'
                        
                        if src and src not in image_urls:
                            image_urls.append(src)
                            print(f"      ✅ 이미지 {len(image_urls)}: {src[:60]}...")
                            
                            if len(image_urls) >= 6:
                                break
                                
                    except Exception as e:
                        print(f"      ⚠️ 이미지 {idx+1} 추출 실패: {e}")
                        continue
            else:
                # 썸네일 없으면 메인 이미지 직접 가져오기
                print("   ℹ️  썸네일 없음 - 메인 이미지 직접 추출")
                selectors = [
                    'img.TgO1N1wWTm[alt="대표이미지"]',
                    'img.TgO1N1wWTm',
                    'div._2LuLme7XCi img',
                ]
                
                for selector in selectors:
                    try:
                        main_img = self.driver.find_element(By.CSS_SELECTOR, selector)
                        src = main_img.get_attribute('src')
                        
                        if src:
                            if '?type=' in src:
                                src = src.split('?type=')[0] + '?type=f640'
                            image_urls.append(src)
                            print(f"      ✅ 메인 이미지: {src[:60]}...")
                            break
                    except:
                        continue
            
            print(f"   ✅ 총 {len(image_urls)}개 대표 이미지 추출 완료")
            return image_urls
            
        except Exception as e:
            print(f"   ⚠️ 이미지 추출 오류: {e}")
            return []
