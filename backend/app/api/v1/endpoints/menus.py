from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.db.session import get_db
from app.db import models
from app.schemas.response import DailyMenuResponse, CafeteriaResponse, MenuResponse

router = APIRouter()

@router.get("/daily", response_model=DailyMenuResponse)
async def get_daily_menu(
    school_name: str = Query(..., description="학교 이름 (예: KAIST)"),
    target_date: date = Query(..., description="날짜 (예: 2026-01-16)"),
    db: AsyncSession = Depends(get_db)
):
    # 1. 학교 찾기
    result = await db.execute(select(models.School).where(models.School.name == school_name))
    school = result.scalars().first()
    
    if not school:
        raise HTTPException(status_code=404, detail="해당 학교를 찾을 수 없습니다.")

    # 2. 그 학교의 식당들 찾기
    result = await db.execute(select(models.Cafeteria).where(models.Cafeteria.school_id == school.id))
    cafeterias = result.scalars().all()
    
    cafeteria_responses = []

    # 3. 각 식당별로 해당 날짜 메뉴 찾기
    for caf in cafeterias:
        result = await db.execute(
            select(models.Menu)
            .where(models.Menu.cafeteria_id == caf.id)
            .where(models.Menu.date == target_date)
        )
        menus = result.scalars().all()
        
        # 메뉴가 있는 경우에만 리스트에 추가
        if menus:
            menu_list = [
                MenuResponse(
                    meal_type=m.meal_type,
                    menu_text=m.menu_text,
                    image_url_3d=m.image_url_3d
                ) for m in menus
            ]
            cafeteria_responses.append(CafeteriaResponse(name=caf.name, menus=menu_list))

    # 4. 최종 결과 반환
    return DailyMenuResponse(
        school_name=school.name,
        date=target_date,
        cafeterias=cafeteria_responses
    )