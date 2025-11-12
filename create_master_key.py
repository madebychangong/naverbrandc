"""
마스터 키 파일 생성 스크립트
- FIREBASE_MASTER_KEY를 base85로 인코딩
- master.key 파일로 저장
- EXE 빌드 시 포함
"""

import os
import base64

def create_master_key_file():
    """마스터 키 파일 생성"""
    print("=" * 70)
    print("🔑 마스터 키 파일 생성")
    print("=" * 70)
    
    # 1. 환경변수에서 마스터 키 읽기
    master_key = os.environ.get('FIREBASE_MASTER_KEY', '')
    
    if not master_key:
        print("\n❌ FIREBASE_MASTER_KEY 환경변수가 설정되지 않았습니다!")
        print("\n설정 방법:")
        print("  set FIREBASE_MASTER_KEY=당신의키")
        print("\n또는 직접 입력:")
        master_key = input("마스터 키를 입력하세요: ").strip()
        
        if not master_key:
            print("❌ 마스터 키가 비어있습니다. 종료합니다.")
            return False
    
    print(f"\n✅ 마스터 키 확인: {master_key[:10]}...{master_key[-10:]}")
    
    # 2. Base85로 인코딩 (난독화)
    try:
        encoded = base64.b85encode(master_key.encode()).decode()
        print(f"✅ Base85 인코딩 완료")
    except Exception as e:
        print(f"❌ 인코딩 실패: {e}")
        return False
    
    # 3. master.key 파일로 저장
    try:
        with open('master.key', 'w', encoding='utf-8') as f:
            f.write(encoded)
        print(f"✅ master.key 파일 생성 완료")
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False
    
    # 4. 검증
    try:
        with open('master.key', 'r', encoding='utf-8') as f:
            test_encoded = f.read().strip()
        
        test_decoded = base64.b85decode(test_encoded).decode()
        
        if test_decoded == master_key:
            print(f"✅ 검증 성공: 인코딩/디코딩 정상")
        else:
            print(f"❌ 검증 실패: 원본과 다름")
            return False
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False
    
    # 5. 완료
    print("\n" + "=" * 70)
    print("🎉 마스터 키 파일 생성 완료!")
    print("=" * 70)
    print(f"\n📁 생성된 파일: master.key")
    print(f"📦 파일 크기: {len(encoded)} bytes")
    print(f"\n📝 다음 단계:")
    print(f"   1. ColdAPP.spec에 master.key 추가 확인")
    print(f"   2. pyinstaller ColdAPP.spec 실행")
    print(f"   3. 생성된 EXE 테스트")
    print(f"\n⚠️  주의사항:")
    print(f"   ✅ master.key는 Git에 커밋하지 마세요")
    print(f"   ✅ .gitignore에 master.key 추가하세요")
    print(f"   ✅ 원본 마스터 키는 안전하게 보관하세요")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = create_master_key_file()
    
    if success:
        print("\n✅ 모든 작업이 완료되었습니다!")
    else:
        print("\n❌ 작업 실패")
        exit(1)
