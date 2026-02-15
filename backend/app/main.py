from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from pytz import timezone

# APScheduler 관련 임포트 변경 (Background -> AsyncIO)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.session import AsyncSessionLocal, engine
from app.db.models import Base
from app.api.v1.endpoints import menus, inquiry
from app.services.auto_filler import AutoFiller

from app.db.init_data import initialize_school_data

from app.services.db_service import delete_old_menus

# 1. 스케줄러 인스턴스 생성 (AsyncIO 전용!)
scheduler = AsyncIOScheduler()

# 👇 [핵심] 스케줄러가 실행할 함수 (이제 async def로 만들어도 됨!)
async def scheduled_crawling_job():
    print("⏰ [스케줄러] 정기 크롤링 시작 (00:01)")
    
    # 스케줄러는 요청(Request) 컨텍스트가 없으니까 세션을 직접 만들어야 해
    try:
        async with AsyncSessionLocal() as session:
            filler = AutoFiller()
            # AutoFiller 안에 크롤링 로직이 있다고 가정 (execute 메서드)
            await filler.execute(session)
            print("✅ [스케줄러] 데이터 업데이트 완료")
    except Exception as e:
        print(f"❌ [스케줄러] 실행 중 에러 발생: {e}")

async def scheduled_cleanup_job():
    print("🧹 [스케줄러] DB 청소 시작 (오래된 데이터 삭제)")
    try:
        async with AsyncSessionLocal() as session:
            # 3일 지난 메뉴 삭제
            await delete_old_menus(session, days=3)
    except Exception as e:
        print(f"❌ [스케줄러] 청소 중 에러 발생: {e}")

# 2. 수명 주기(Lifespan) 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # (1) DB 테이블 생성
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # print("✅ DB 테이블 체크 완료")

    async with AsyncSessionLocal() as session:
        await initialize_school_data(session)

    # (2) 스케줄러 설정 및 시작
    # 매일 00:01분에 실행
    scheduler.add_job(
        scheduled_crawling_job, 
        CronTrigger(hour=0, minute=1, timezone=timezone('Asia/Seoul')),
        id="daily_crawling",
        replace_existing=True
    )

    scheduler.add_job(
        scheduled_cleanup_job,
        CronTrigger(hour=0, minute=31, timezone=timezone('Asia/Seoul')),
        id="daily_cleanup",
        replace_existing=True
    )

    scheduler.start()
    print("🚀 [시스템] 비동기 스케줄러 가동됨 (매일 00:01 실행)")

    # (3) 서버 시작 시 한 번 실행해보고 싶으면 주석 해제 (테스트용)
    # asyncio.create_task(scheduled_crawling_job())
    
    yield # 서버 가동 중...
    
    # [꺼질 때 실행할 코드]
    scheduler.shutdown()
    print("👋 서버 및 스케줄러 종료.")

# 3. FastAPI 앱 생성
app = FastAPI(
    title="학식 요정 백엔드",
    description="너를 위한 3D 학식 알리미 API 서버",
    version="0.0.3", # 버전 업!
    lifespan=lifespan
)

# 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(menus.router, prefix="/api/v1", tags=["menus"])
app.include_router(inquiry.router, prefix="/api/v1/inquiries", tags=["inquiries"])

@app.get("/")
def read_root():
    return {"message": "서버 정상 작동 중! 스케줄러도 비동기로 쌩쌩 돌아갑니다."}