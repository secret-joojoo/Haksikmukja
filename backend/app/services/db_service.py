import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db import models
from app.schemas.crawler import SchoolData

async def save_school_data(session: AsyncSession, data: SchoolData):
    # 1. 학교가 이미 있는지 확인
    result = await session.execute(select(models.School).where(models.School.name == data.school_name))
    school = result.scalars().first()

    # 없으면 새로 생성
    if not school:
        school = models.School(name=data.school_name, region=data.school_region)
        session.add(school)
        await session.flush() # ID를 발급받기 위해 임시 저장

    # 2. 식당 처리
    for caf_data in data.cafeterias:
        result = await session.execute(
            select(models.Cafeteria)
            .where(models.Cafeteria.school_id == school.id)
            .where(models.Cafeteria.name == caf_data.name)
        )
        cafeteria = result.scalars().first()

        if not cafeteria:
            cafeteria = models.Cafeteria(school_id=school.id, name=caf_data.name)
            session.add(cafeteria)
            await session.flush()

        # 3. 메뉴 저장 (덮어쓰기 로직)
        # 3. 메뉴 저장 로직 수정
        for menu_data in caf_data.menus:
            
            # [전처리] 
            # 1. 알레르기 정보 제거: "두부계란국(1,5)" -> "두부계란국"
            cleaned_items = [re.sub(r'\([0-9.,]+\)', '', item).strip() for item in menu_data.menu_items]
            
            # 2. 리스트를 줄바꿈 문자로 합치기: ["밥", "국"] -> "밥\n국"
            final_menu_text = "\n".join(cleaned_items)

            # 해당 날짜, 해당 식사(점심/저녁)에 이미 메뉴가 있는지 확인
            result = await session.execute(
                select(models.Menu)
                .where(models.Menu.cafeteria_id == cafeteria.id)
                .where(models.Menu.date == menu_data.date)
                .where(models.Menu.meal_type == menu_data.meal_type)
            )
            existing_menu = result.scalars().first()

            if existing_menu:
                existing_menu.menu_text = final_menu_text # 합친 문자열 저장
            else:
                new_menu = models.Menu(
                    cafeteria_id=cafeteria.id,
                    date=menu_data.date,
                    meal_type=menu_data.meal_type,
                    menu_text=final_menu_text # 합친 문자열 저장
                )
                session.add(new_menu)
    
    # 최종 저장
    await session.commit()
    print(f"✅ {data.school_name} 데이터 저장 완료!")

async def delete_old_menus(db: AsyncSession, days: int = 3):
    """
    기준 일수(days)보다 오래된 메뉴 데이터를 삭제합니다.
    기본값: 3일
    """
    # 1. 기준 날짜 계산 (오늘 - 3일)
    cutoff_date = (datetime.now() - timedelta(days=days)).date()
    
    print(f"🧹 [청소] {cutoff_date} 이전의 오래된 메뉴를 삭제합니다...")

    # 2. 삭제 쿼리 실행
    # "Menu.date < cutoff_date" 인 녀석들만 골라서 삭제
    result = await db.execute(delete(Menu).where(Menu.date < cutoff_date))
    
    # 3. 변경사항 저장
    await db.commit()
    
    deleted_count = result.rowcount
    print(f"✨ [청소 완료] 총 {deleted_count}개의 유통기한 지난 메뉴가 삭제되었습니다.")
    return deleted_count