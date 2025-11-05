"""
ColdAPP 설정 관리자
- AppData\Roaming\ColdAPP\config.json에 설정 저장
- 네이버/티스토리 설정
- 로그인 이메일 저장
"""

import json
import os


class ConfigManager:
    """ColdAPP 설정 및 로그인 이메일 저장 관리자"""

    CONFIG_DIR = os.path.join(os.getenv("APPDATA"), "ColdAPP")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    @staticmethod
    def ensure_dir():
        """폴더가 없으면 자동 생성"""
        if not os.path.exists(ConfigManager.CONFIG_DIR):
            os.makedirs(ConfigManager.CONFIG_DIR, exist_ok=True)

    @staticmethod
    def load():
        """설정 파일 불러오기"""
        ConfigManager.ensure_dir()
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        # 기본 구조 반환
        return {
            "blog_id": "",
            "naver_id": "",
            "naver_pw": "",
            "gemini_api_key": "",
            "last_login_email": "",
            "tistory_access_token": "",
            "tistory_blog_name": "",
            "use_naver": True,
            "use_tistory": False
        }

    @staticmethod
    def save(config):
        """설정 파일 저장"""
        ConfigManager.ensure_dir()
        with open(ConfigManager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def save_login_email(email: str):
        """Firebase 로그인 이메일만 저장"""
        config = ConfigManager.load()
        config["last_login_email"] = email
        ConfigManager.save(config)

    @staticmethod
    def load_login_email() -> str:
        """저장된 Firebase 로그인 이메일 불러오기"""
        config = ConfigManager.load()
        return config.get("last_login_email", "")
