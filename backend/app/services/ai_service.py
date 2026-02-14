from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import models
from app.services.ai_generator.prompter import MenuPrompter
from app.services.ai_generator.client import ImageGenerator

class AIService:
    def __init__(self):
        self.prompter = MenuPrompter()
        self.generator = ImageGenerator()

    async def generate_daily_images(self, session: AsyncSession, target_date, school_name: str = None):
        """
        [트랜잭션 최적화 버전]
        메뉴 이미지를 생성하고, 일정 개수(BATCH_SIZE)마다 모아서 커밋합니다.
        """
        BATCH_SIZE = 5 # 5개씩 묶어서 저장 (DB 부하 감소 + 너무 긴 트랜잭션 방지)
        
        print(f"🚀 {target_date} 메뉴 이미지 생성 시작 (대상: {school_name or '전체'})...")

        stmt = select(models.Menu).join(models.Cafeteria).join(models.School).where(
            models.Menu.date == target_date,
            models.Menu.image_url_3d == None 
        )

        if school_name:
            stmt = stmt.where(models.School.name == school_name)

        result = await session.execute(stmt)
        menus = result.scalars().all()

        if not menus:
            print(f"💤 생성할 대상이 없습니다.")
            return

        total_count = len(menus)
        print(f"⚡ 총 {total_count}개의 메뉴 이미지 생성을 시작합니다.")

        # 처리 카운터
        processed_count = 0

        for menu in menus:
            try:
                # 1. 이미지 생성 (AI 호출 - 시간 소요됨)
                menu_items_list = menu.menu_text.split("\n")
                prompt = await self.prompter.create_prompt(menu_items_list, menu.meal_type)
                image_url = await self.generator.generate_image(prompt)
                
                # 2. 메모리에 반영 (아직 DB에는 안 감)
                menu.image_url_3d = image_url
                session.add(menu)
                
                processed_count += 1

                # 3. [핵심] 배치 사이즈만큼 찼을 때만 커밋!
                if processed_count % BATCH_SIZE == 0:
                    await session.commit()
                    print(f"   -> {processed_count}/{total_count}개 저장 완료...")

            except Exception as e:
                print(f"❌ 이미지 생성 중 에러 (ID: {menu.id}): {e}")
                # 에러 나도 다음 메뉴는 계속 진행해야 하니까 멈추지 않음

        # 4. 반복문 끝나고 남은 찌꺼기들 최종 커밋
        if processed_count % BATCH_SIZE != 0:
            await session.commit()
        
        print(f"🎉 이미지 생성 작업 최종 완료! (총 {processed_count}개)")