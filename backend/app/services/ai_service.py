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
        school_name이 있으면 그 학교 것만 처리.
        이미지가 이미 있는 건(image_url_3d IS NOT NULL) 건너뜀.
        """
        
        print(f"🚀 {target_date} 메뉴 이미지 생성 시작 (대상: {school_name or '전체'})...")

        # 쿼리 작성
        stmt = select(models.Menu).join(models.Cafeteria).join(models.School).where(
            models.Menu.date == target_date,
            models.Menu.image_url_3d == None  # ✅ 중요: 이미지가 없는 것만 조회!
        )

        # 학교 필터가 있으면 적용
        if school_name:
            stmt = stmt.where(models.School.name == school_name)

        result = await session.execute(stmt)
        menus = result.scalars().all()

        if not menus:
            print(f"💤 생성할 대상이 없습니다. (모두 완료되었거나 데이터 없음)")
            return

        print(f"⚡ 총 {len(menus)}개의 메뉴에 대해 이미지 생성을 시작합니다.")

        for menu in menus:
            try:
                # 메뉴 텍스트 리스트화
                menu_items_list = menu.menu_text.split("\n")
                
                # 프롬프트 생성 (meal_type 전달)
                prompt = await self.prompter.create_prompt(menu_items_list, menu.meal_type)
                
                # 이미지 생성
                image_url = await self.generator.generate_image(prompt)
                
                # DB 업데이트
                menu.image_url_3d = image_url
                session.add(menu)
                
                # 너무 자주 커밋하면 느리니까 적당히 모아서 해도 되지만, 안전하게 매번 커밋
                await session.commit() 
            except Exception as e:
                print(f"❌ 이미지 생성 중 에러 (ID: {menu.id}): {e}")

        print("🎉 이미지 생성 작업 완료!")