from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db import models
from app.services.crawler.scrapers import get_scrapers 
from app.services.db_service import save_school_data
from app.services.ai_service import AIService

class AutoFiller:
    def __init__(self):
        self.scrapers = get_scrapers() 
        self.ai_service = AIService()

    async def execute(self, session: AsyncSession):
        """
        등록된 모든 학교에 대해 크롤링 및 데이터 무결성 검사 수행
        """
        today = date.today()
        check_dates = [today + timedelta(days=i) for i in range(-1, 3)] # 어제 ~ 모레

        print(f"🔄 [AutoFiller] 전체 학교 데이터 동기화 시작")

        for scraper in self.scrapers:
            school_name = scraper.school_name
            print(f"  🏫 학교 점검: {school_name}")

            for target_date in check_dates:
                # 1. DB에 데이터가 있는지 개수 확인
                stmt = select(func.count(models.Menu.id)) \
                    .join(models.Cafeteria).join(models.School) \
                    .where(
                        models.School.name == school_name,
                        models.Menu.date == target_date
                    )
                
                result = await session.execute(stmt)
                menu_count = result.scalar() or 0

                # 🔴 [수정 핵심] 스킵 조건 강화!
                # "어제(과거)" 데이터는 이미 지나갔으니 굳이 다시 안 긁어도 돼. (있으면 패스)
                if target_date < today and menu_count > 0:
                    print(f"    ✅ {target_date}: 과거 데이터 있음 ({menu_count}개) (Skip)")
                    continue
                
                # 하지만 "오늘/미래" 데이터는?
                # 1. '학생식당'은 있는데 '교직원식당'이 늦게 올라왔을 수도 있고 (부분 누락)
                # 2. 메뉴가 중간에 수정됐을 수도 있어. (반찬 변경 등)
                # 그러니까 '데이터가 있어도' 게으름 피우지 말고 무조건 다시 긁어오라고 시키는 거야!
                
                status_msg = f"기존 {menu_count}개 발견" if menu_count > 0 else "데이터 없음"
                print(f"    ⚡ {target_date}: 동기화 시도 ({status_msg}) -> 크롤링 재수행")
                
                try:
                    # (1) 크롤링 (무조건 실행)
                    school_data = await scraper.parse(target_date)
                    
                    if school_data:
                        # (2) DB 저장
                        # 걱정 마, db_service.py에 '덮어쓰기(Update)' 로직이 있어서 데이터 중복 안 돼!
                        await save_school_data(session, school_data)
                        
                        # (3) AI 이미지 생성 (필요하면)
                        await self.ai_service.generate_daily_images(session, target_date)
                        print(f"       -> 동기화 완료.")
                    else:
                        print(f"       -> ⚠️ 데이터 수집 실패 (사이트 응답 없음 or 휴일)")

                except Exception as e:
                    print(f"       ❌ 에러 발생: {e}")

        print("✨ [AutoFiller] 모든 작업 완료!")