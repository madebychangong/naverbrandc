# -*- mode: python ; coding: utf-8 -*-

"""
ColdAPP - 네이버 블로그 자동화 프로그램
단일 EXE 파일 빌드 설정 (Web API Config 방식)
"""

block_cipher = None

a = Analysis(
    ['main_gui4.py'],  # 메인 파일
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # assets 폴더를 EXE에 포함
        ('firebase_config.enc', '.'),  # 암호화된 Firebase 설정 파일 포함
        ('master.key', '.'),  # 마스터 키 파일 포함 (새로 추가!)
    ],
    hiddenimports=[
        'naver_blog_automation',  # 추가 모듈
        'firebase_auth',          # 추가 모듈 (Web API 방식)
        'cryptography',           # 암호화 라이브러리
        'cryptography.fernet',    # Fernet 암호화
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'requests',               # REST API 통신
        'json',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',                  # PyQt5 제외 (PyQt6 사용)
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ColdAPP',  # EXE 파일 이름
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 파일 압축 (용량 줄이기)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='coldapp_icon.ico',  # EXE 아이콘 (.ico 파일)
)
