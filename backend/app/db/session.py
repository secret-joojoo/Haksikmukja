from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from app.core.config import settings

# 1. SQLite 전용 설정 (쓰레드 에러 방지)
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

# 2. 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # 로그 보기
    connect_args=connect_args
)

# 3. 세션 생성기
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 🔴 [복구 완료] 이 함수가 없어서 아까 에러가 났던 거야!
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session