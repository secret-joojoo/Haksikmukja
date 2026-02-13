import asyncio
import sys
import os

# 현재 경로(backend)를 파이썬 패스에 추가해서 app 모듈을 찾을 수 있게 함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from app.db.base import Base
from app.db import models # 🔴 이걸 임포트해야 테이블 정보가 Base에 등록돼!

async def reset_database():
    print("💣 데이터베이스 초기화 시작...")
    
    async with engine.begin() as conn:
        # 1. 모든 테이블 삭제 (순서대로 싹 날림)
        print("🗑️ 기존 테이블 삭제 중...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # 2. 테이블 다시 생성
        print("✨ 새 테이블 생성 중...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("✅ 초기화 완료! 이제 아주 깨끗해졌어.")

if __name__ == "__main__":
    # 윈도우 사용자라면 이벤트 루프 정책 설정이 필요할 수 있어
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(reset_database())