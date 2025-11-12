"""
Firebase 인증 시스템 (Web API Config 방식)
- Web API Config만 사용 (Service Account Key 불필요)
- Security Rules로 권한 관리  
- IP + 로그인 시간 자동 기록
- ColdHawk와 동일한 보안 구조
- REST API 직접 사용 (추가 패키지 불필요)
"""

from datetime import datetime, timedelta, timezone
import json
import os
import sys
import requests


def get_user_ip():
    """사용자의 공인 IP 주소 조회"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=3)
        if response.status_code == 200:
            return response.json().get('ip', 'unknown')
        return 'unknown'
    except:
        return 'unknown'


class FirebaseAuthManager:
    """Firebase 인증 관리자 (Web API Config 방식 - REST API)"""
    
    def __init__(self, config_path='firebase_config.json'):
        """
        Firebase 초기화 (Web API Config)
        
        Args:
            config_path: Firebase Web API 설정 파일 경로
        """
        self.api_key = None
        self.project_id = None
        self.initialized = False
        
        # 암호화된 파일 경로
        if hasattr(sys, '_MEIPASS'):
            # EXE 환경
            config_path = os.path.join(sys._MEIPASS, 'firebase_config.json')
            encrypted_path = os.path.join(sys._MEIPASS, 'firebase_config.enc')
        else:
            # 개발 환경
            encrypted_path = 'firebase_config.enc'
        
        # 설정 파일 로드
        firebase_config = None
        
        if os.path.exists(encrypted_path):
            print(f"🔐 암호화된 Firebase 설정 발견: {encrypted_path}")
            firebase_config = self._load_encrypted_config(encrypted_path)
        elif os.path.exists(config_path):
            print(f"📄 Firebase 설정 파일 사용: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                firebase_config = json.load(f)
        else:
            print(f"⚠️ Firebase 설정 파일이 없습니다")
            return
        
        if not firebase_config or firebase_config.get('disabled'):
            print("⚠️ Firebase가 비활성화되어 있습니다")
            return
        
        try:
            self.api_key = firebase_config.get('apiKey')
            self.project_id = firebase_config.get('projectId')
            
            if self.api_key and self.project_id:
                self.initialized = True
                print("✅ Firebase 초기화 완료 (Web API Config - REST API)")
            else:
                print("⚠️ Firebase 설정이 불완전합니다")
            
        except Exception as e:
            print(f"⚠️ Firebase 초기화 실패: {e}")
    
    def _load_encrypted_config(self, encrypted_path):
        """암호화된 설정 로드 (AES-256)"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64
            
            # 마스터 키 (환경변수 또는 master.key 파일)
            master_password = os.environ.get('FIREBASE_MASTER_KEY', '')
            
            if not master_password:
                # master.key 파일에서 읽기
                try:
                    if hasattr(sys, '_MEIPASS'):
                        key_path = os.path.join(sys._MEIPASS, 'master.key')
                    else:
                        key_path = 'master.key'
                    
                    if os.path.exists(key_path):
                        with open(key_path, 'r', encoding='utf-8') as f:
                            encoded_key = f.read().strip()
                        master_password = base64.b85decode(encoded_key).decode()
                        print("✅ master.key 파일에서 키 로드")
                    else:
                        print("⚠️ FIREBASE_MASTER_KEY 환경변수와 master.key 파일이 모두 없습니다")
                        return None
                except Exception as e:
                    print(f"❌ master.key 파일 읽기 실패: {e}")
                    return None
            
            if not master_password:
                print("⚠️ 마스터 키를 찾을 수 없습니다")
                return None
            
            # 키 생성
            salt = b'ColdHawk_Firebase_2024_Salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            
            # 복호화
            fernet = Fernet(key)
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            config = json.loads(decrypted_data.decode('utf-8'))
            
            print("✅ 설정 파일 복호화 완료")
            return config
            
        except Exception as e:
            print(f"❌ 복호화 실패: {e}")
            return None
    
    def is_enabled(self):
        """Firebase 활성화 확인"""
        return self.initialized
    
    def _sign_in_with_email_password(self, email, password):
        """
        Firebase Authentication REST API로 로그인
        
        Returns:
            dict: {'idToken': ..., 'localId': ..., 'email': ...} 또는 None
        """
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'UNKNOWN_ERROR')
                print(f"❌ 로그인 실패: {error_msg}")
                return None
                
        except Exception as e:
            print(f"❌ 로그인 요청 오류: {e}")
            return None
    
    def _get_firestore_document(self, collection, document_id, id_token):
        """
        Firestore 문서 조회 (REST API)
        
        Returns:
            dict: 문서 데이터 또는 None
        """
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}/{document_id}"
            headers = {
                "Authorization": f"Bearer {id_token}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                doc_data = response.json()
                # Firestore 형식을 일반 dict로 변환
                return self._convert_firestore_fields(doc_data.get('fields', {}))
            else:
                print(f"⚠️ 문서 조회 실패: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 문서 조회 오류: {e}")
            return None
    
    def _update_firestore_document(self, collection, document_id, id_token, fields):
        """
        Firestore 문서 업데이트 (REST API)
        
        Args:
            fields: dict - 업데이트할 필드들 {'field_name': value}
        """
        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}/{document_id}"
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }
            
            # Firestore 형식으로 변환
            firestore_fields = self._convert_to_firestore_fields(fields)
            
            payload = {
                "fields": firestore_fields
            }
            
            # updateMask 생성
            update_mask = ",".join(fields.keys())
            params = {"updateMask.fieldPaths": list(fields.keys())}
            
            response = requests.patch(url, headers=headers, json=payload, params=params, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ 문서 업데이트 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 문서 업데이트 오류: {e}")
            return False
    
    def _convert_firestore_fields(self, fields):
        """Firestore 형식을 일반 dict로 변환"""
        result = {}
        for key, value in fields.items():
            if 'stringValue' in value:
                result[key] = value['stringValue']
            elif 'integerValue' in value:
                result[key] = int(value['integerValue'])
            elif 'booleanValue' in value:
                result[key] = value['booleanValue']
            elif 'timestampValue' in value:
                result[key] = value['timestampValue']
            elif 'doubleValue' in value:
                result[key] = float(value['doubleValue'])
            else:
                result[key] = value
        return result
    
    def _convert_to_firestore_fields(self, data):
        """일반 dict를 Firestore 형식으로 변환"""
        fields = {}
        for key, value in data.items():
            if isinstance(value, str):
                fields[key] = {'stringValue': value}
            elif isinstance(value, bool):
                fields[key] = {'booleanValue': value}
            elif isinstance(value, int):
                fields[key] = {'integerValue': str(value)}
            elif isinstance(value, float):
                fields[key] = {'doubleValue': value}
            elif isinstance(value, datetime):
                # 시간대 정보가 있으면 그대로, 없으면 Z 추가
                if value.tzinfo is not None:
                    fields[key] = {'timestampValue': value.isoformat()}
                else:
                    fields[key] = {'timestampValue': value.isoformat() + 'Z'}
            else:
                fields[key] = {'stringValue': str(value)}
        return fields
    
    def verify_user(self, email, password):
        """
        사용자 인증 + IP/시간 기록
        
        Args:
            email: 이메일
            password: 비밀번호
            
        Returns:
            dict: 사용자 정보 또는 에러
        """
        if not self.is_enabled():
            return {'error': 'Firebase가 초기화되지 않았습니다'}
        
        try:
            # 1. Firebase Authentication으로 로그인
            auth_result = self._sign_in_with_email_password(email, password)
            
            if not auth_result:
                return {'error': '이메일 또는 비밀번호가 일치하지 않습니다'}
            
            id_token = auth_result.get('idToken')
            user_id = auth_result.get('localId')  # UID 가져오기
            
            # 2. Firestore에서 사용자 정보 조회 (UID로)
            user_data = self._get_firestore_document('users', user_id, id_token)
            
            if not user_data:
                return {'error': '사용자 정보를 찾을 수 없습니다'}
            
            # 3. 상태 확인
            is_active = user_data.get('is_active')
            if is_active is not None and not is_active:
                return {'error': '계정이 비활성화되었습니다'}
            
            status = user_data.get('status')
            if status and status != 'approved':
                if status == 'pending':
                    return {'error': '관리자 승인 대기 중입니다'}
                elif status == 'suspended':
                    return {'error': '계정이 일시정지되었습니다'}
                else:
                    return {'error': f'계정 상태: {status}'}
            
            # 4. 만료일 확인
            expiry_date = user_data.get('expiryDate') or user_data.get('expiry_date')
            if expiry_date:
                try:
                    if isinstance(expiry_date, str):
                        expiry_date = datetime.fromisoformat(expiry_date.replace('Z', ''))
                    
                    if expiry_date and datetime.now() > expiry_date:
                        return {'error': '사용 기간이 만료되었습니다'}
                except:
                    expiry_date = None
            
            # 5. IP + 시간 기록 (Security Rules로 허용됨)
            try:
                current_ip = get_user_ip()
                # 한국 시간 (UTC+9) 명시적으로 저장
                kst = timezone(timedelta(hours=9))
                current_time = datetime.now(kst)
                
                update_fields = {
                    'lastLogin': current_time,
                    'lastLoginAt': current_time,
                    'lastLoginIP': current_ip,
                    'lastUsed': current_time
                }
                
                self._update_firestore_document('users', user_id, id_token, update_fields)
                print(f"✅ 로그인 정보 기록: {email} (UID: {user_id[:10]}...) / IP: {current_ip}")
            except Exception as e:
                print(f"⚠️ 로그인 정보 기록 실패 (무시): {e}")
            
            # 6. 사용자 정보 반환
            return {
                'email': email,
                'name': user_data.get('nickname') or user_data.get('name', ''),
                'plan': user_data.get('plan', 'free'),
                'expiry_date': expiry_date,
                'usage_count': user_data.get('usage_count', 0),
                'usage_limit': user_data.get('usage_limit', 10),
                'is_active': is_active if is_active is not None else True,
                'id_token': id_token,
                'signupIP': user_data.get('signupIP', user_data.get('signup_ip', 'N/A')),  # ← 추가
                'last_login_ip': current_ip  # ← 현재 로그인 IP
            }
            
        except Exception as e:
            print(f"❌ 인증 오류: {e}")
            return {'error': f'로그인 실패: {str(e)}'}
    
    def check_usage_limit(self, email):
        """사용 횟수 제한 확인 (무제한)"""
        return True
    
    def increment_usage(self, email, id_token=None):
        """
        사용 횟수 증가
        
        Args:
            email: 이메일
            id_token: 인증 토큰 (옵션)
        """
        if not id_token:
            print("⚠️ 토큰 없음 - 사용 횟수 업데이트 건너뜀")
            return
        
        try:
            # 현재 값 조회 후 증가
            user_data = self._get_firestore_document('users', email, id_token)
            if user_data:
                current_count = user_data.get('usage_count', 0)
                # 한국 시간 (UTC+9) 명시적으로 저장
                kst = timezone(timedelta(hours=9))
                current_time = datetime.now(kst)
                
                update_fields = {
                    'usage_count': current_count + 1,
                    'lastUsed': current_time
                }
                self._update_firestore_document('users', email, id_token, update_fields)
                print(f"✅ 사용 횟수 증가: {email}")
        except Exception as e:
            print(f"⚠️ 사용 횟수 업데이트 실패: {e}")
    
    def get_user_info(self, email, id_token):
        """
        사용자 정보 조회
        
        Args:
            email: 이메일
            id_token: 인증 토큰
        """
        return self._get_firestore_document('users', email, id_token)


# 테스트 코드
if __name__ == "__main__":
    auth_manager = FirebaseAuthManager()
    
    if auth_manager.is_enabled():
        print("\n🔥 Firebase 인증 시스템 활성화됨 (Web API Config)")
        print("   ✅ IP + 로그인 시간 자동 기록")
        print("   ✅ Security Rules로 권한 제어")
    else:
        print("\n⚠️ Firebase가 비활성화되어 있습니다")
