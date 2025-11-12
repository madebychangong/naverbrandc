"""
이미지 처리 모듈
- 이미지 다운로드 (상품 이미지 + 상세 설명 이미지)
- base64 인코딩 (Gemini Vision API용)
- 이미지 파일 관리
"""

import os
import requests
import base64


class ImageHandler:
    """이미지 다운로드 및 처리 클래스"""
    
    def __init__(self, temp_dir='temp_images'):
        """
        초기화
        
        Args:
            temp_dir: 임시 이미지 저장 폴더 경로
        """
        self.temp_dir = temp_dir
        
        # temp_images 폴더 생성
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            print(f"✅ 임시 폴더 생성: {self.temp_dir}")
    
    def download_product_images(self, image_urls):
        """
        상품 대표 이미지들 다운로드
        
        Args:
            image_urls: 이미지 URL 리스트
            
        Returns:
            list: 다운로드된 파일 경로 리스트
        """
        print(f"\n💾 상품 이미지 다운로드 중...")
        print(f"   📊 다운로드할 이미지: {len(image_urls)}개")
        
        if not image_urls:
            print("   ⚠️ 이미지 URL이 없습니다!")
            return []
        
        downloaded_files = []
        
        for idx, url in enumerate(image_urls):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    filename = f"product_{idx+1}.jpg"
                    filepath = os.path.join(self.temp_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    abs_path = os.path.abspath(filepath)
                    downloaded_files.append(abs_path)
                    print(f"   ✅ {filename} 다운로드 완료")
                    
            except Exception as e:
                print(f"   ⚠️ 이미지 {idx+1} 다운로드 실패: {e}")
                continue
        
        print(f"✅ {len(downloaded_files)}개 상품 이미지 다운로드 완료")
        return downloaded_files
    def encode_image_to_base64(self, image_path):
        """
        이미지 파일을 base64로 인코딩
        (Gemini Vision API가 이미지를 받을 때 필요)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            str: base64 인코딩된 문자열 (실패 시 None)
        """
        try:
            with open(image_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            print(f"   ⚠️ 이미지 인코딩 실패 ({image_path}): {e}")
            return None
    
    def prepare_images_for_vision(self, image_paths):
        """
        여러 이미지를 Vision API용으로 준비
        (PIL Image 객체로 변환)
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            
        Returns:
            list: PIL.Image 객체 리스트
        """
        from PIL import Image
        
        images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                images.append(img)
            except Exception as e:
                print(f"   ⚠️ 이미지 로드 실패 ({path}): {e}")
                continue
        
        print(f"   ✅ {len(images)}개 이미지를 Vision API용으로 준비 완료")
        return images
    
    def cleanup_temp_files(self):
        """
        임시 파일 정리 (선택사항)
        """
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"✅ 임시 파일 정리 완료: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ 임시 파일 정리 실패: {e}")
