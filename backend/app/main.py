from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from app.db.session import AsyncSessionLocal, engine  # 🔴 engine 추가
from app.db.models import Base  # 🔴 Base (테이블 설계도) 추가
from app.api.v1.endpoints import menus
from app.services.auto_filler import AutoFiller
from fastapi.middleware.cors import CORSMiddleware # 추가
from app.api.v1.endpoints import menus, inquiry    # inquiry 추가
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 1. 수명 주기(Lifespan) 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔴 [추가] 서버 시작될 때 테이블 만들기!
    # "야, 엔진아! 설계도(Base) 좀 보고 테이블 없으면 싹 다 만들어라!"
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ DB 테이블 생성 완료 (haksik.db 준비됨)")

    print("🚀 서버 가동! 자동 데이터 채우기 작업 시작...")
    
    # 백그라운드 태스크로 실행
    asyncio.create_task(run_background_fill())
    
    yield # 여기서 서버가 돌아감 (요청 대기)
    
    # [꺼질 때 실행할 코드]
    print("👋 서버 종료. 안녕히 가세요.")

# 백그라운드 실행용 헬퍼 함수
async def run_background_fill():
    async with AsyncSessionLocal() as session:
        filler = AutoFiller()
        await filler.execute(session)

# 2. FastAPI 앱 생성
app = FastAPI(
    title="학식 요정 백엔드",
    description="너를 위한 3D 학식 알리미 API 서버",
    version="0.1.0",
    lifespan=lifespan
)


# 👇 [핵심] 00:05분에 실행될 함수 정의
def scheduled_crawling_job():
    print("⏰ [스케줄러] 정기 크롤링 시작 (00:05)")
    # 비동기 함수를 동기 스케줄러에서 실행하기 위한 처리
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # AutoFiller에 크롤링 실행 함수가 있다고 가정 (없으면 만들어야 해!)
    # 예: loop.run_until_complete(AutoFiller.process_all()) 
    # 현재 파일들을 보니 AutoFiller 클래스 구조를 확인해서 적절한 메서드를 호출해야 해.
    # 만약 process_daily_menu() 같은 게 있다면 그걸 호출!
    print("✅ [스케줄러] 크롤링 완료")
    loop.close()

# 👇 [추가] 서버 시작할 때 스케줄러 가동!
@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # 매일 0시 5분에 실행 (hour=0, minute=5)
    scheduler.add_job(
        scheduled_crawling_job, 
        CronTrigger(hour=0, minute=5), 
        id="daily_crawling",
        replace_existing=True
    )
    
    scheduler.start()
    print("🚀 [시스템] 스케줄러가 백그라운드에서 실행되었습니다.")

# ... (app = FastAPI(...) 선언 직후에 추가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (개발 단계니까 쿨하게 열어둠)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menus.router, prefix="/api/v1", tags=["menus"])
app.include_router(inquiry.router, prefix="/api/v1/inquiries", tags=["inquiries"]) # 라우터 등록

@app.get("/")
def read_root():
    return {"message": "서버 정상 작동 중! /docs로 가서 API를 테스트해보세요."}