from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import contains_eager
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
    # 1. 학교 존재 여부 먼저 확인 (이건 가벼우니까 따로 해도 됨)
    # 쿼리 한 번으로 합칠 수도 있지만, 404 에러를 명확히 주려고 남겨둠
    school_result = await db.execute(select(models.School).where(models.School.name == school_name))
    school = school_result.scalars().first()
    
    if not school:
        raise HTTPException(status_code=404, detail="해당 학교를 찾을 수 없습니다.")

    # 2. [핵심] 식당 + 메뉴(해당 날짜) 한 방에 조회 (Join & Contains Eager)
    # 설명: "식당(Cafeteria)을 찾는데, 메뉴(Menu) 테이블이랑 합쳐(Outer Join). 
    #       단, 메뉴는 날짜가 target_date인 것만 합쳐.
    #       그리고 그 합친 결과(메뉴 데이터)를 파이썬 객체의 .menus 속성에 미리 채워놔(contains_eager)."
    stmt = (
        select(models.Cafeteria)
        .join(models.School)  # 학교로 필터링하기 위해 조인
        .outerjoin(
            models.Menu, 
            and_(
                models.Menu.cafeteria_id == models.Cafeteria.id,
                models.Menu.date == target_date
            )
        )
        .where(models.School.name == school_name)
        .options(contains_eager(models.Cafeteria.menus)) # 👈 이게 마법의 키워드야!
    )

    result = await db.execute(stmt)
    # unique()는 식당이 중복되어 나오는 걸 방지해 (1:N 조인이라서 필수)
    cafeterias = result.unique().scalars().all()
    
    # 3. 데이터 변환 (이제 DB 조회 안 함! 메모리에 있는 거 꺼내 쓰기만 하면 됨)
    cafeteria_responses = []

    for caf in cafeterias:
        # 이미 caf.menus 안에 해당 날짜 메뉴가 들어있음! (쿼리 안 날아감)
        if caf.menus:
            menu_list = [
                MenuResponse(
                    meal_type=m.meal_type,
                    menu_text=m.menu_text,
                    image_url_3d=m.image_url_3d
                ) for m in caf.menus
            ]
            cafeteria_responses.append(CafeteriaResponse(name=caf.name, menus=menu_list))

    # 4. 최종 결과 반환
    return DailyMenuResponse(
        school_name=school.name,
        date=target_date,
        cafeterias=cafeteria_responses
    )