from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# 1. 메뉴 정보 (보여줄 것만 딱 정의)
class MenuResponse(BaseModel):
    meal_type: str         # 조식/중식/석식
    menu_text: str         # "쌀밥\n텐동덮밥..."
    image_url_3d: Optional[str] = None # 나중에 AI가 만든 이미지 URL

# 2. 식당 정보
class CafeteriaResponse(BaseModel):
    name: str              # 식당 이름 (카이마루)
    menus: List[MenuResponse]

# 3. 최종 응답 형태 (학교 + 식당들)
class DailyMenuResponse(BaseModel):
    school_name: str
    date: date
    cafeterias: List[CafeteriaResponse]