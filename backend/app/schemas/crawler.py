from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# 메뉴 하나에 대한 정의
class MenuData(BaseModel):
    meal_type: str        # BREAKFAST, LUNCH, DINNER
    # 기존: menu_text: str 
    # 변경: 메뉴 리스트로 받음 (예: ["백미밥", "된장국", "김치"])
    menu_items: List[str] 
    date: date

# 식당 하나에 대한 정의 (메뉴 리스트를 포함)
class CafeteriaData(BaseModel):
    name: str             # 식당 이름 (예: 학생회관)
    menus: List[MenuData] # 그 식당의 메뉴들

# 학교 하나에 대한 정의 (식당 리스트를 포함)
class SchoolData(BaseModel):
    school_name: str         # 학교 이름 (예: 한국대)
    school_region: str       # 지역 (예: 서울)
    cafeterias: List[CafeteriaData]