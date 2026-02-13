from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import httpx
import asyncio
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class EwhaScraper(BaseScraper):
    CAFETERIAS = [
        {"name": "I-House 학생식당", "no": "339841"},
        {"name": "진·선·미관 식당", "no": "903"},
        {"name": "공대식당", "no": "905"},
        {"name": "한우리집 식당", "no": "899"},
        {"name": "E-House 식당(201동)", "no": "900"},
    ]

    def __init__(self):
        super().__init__(
            school_name="이화여자대학교",
            school_region="서울",
            url="https://www.ewha.ac.kr/ewha/life/restaurant.do"
        )

    async def fetch_html(self, article_no: str, target_date: date):
        # 💡 날짜 파라미터를 srDt로 넘기더라도 서버 응답은 전체 주간 데이터를 포함할 수 있음
        formatted_date = target_date.strftime("%Y-%m-%d")
        target_url = (
            f"{self.url}?mode=view&articleNo={article_no}"
            f"&article.offset=0&articleLimit=10&srDt={formatted_date}"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.ewha.ac.kr/ewha/life/restaurant.do"
        }

        async with httpx.AsyncClient(verify=False, headers=headers, timeout=15.0) as client:
            try:
                response = await client.get(target_url)
                return response.text if response.status_code == 200 else None
            except Exception as e:
                print(f"❌ [이화여자대학교] 접속 에러: {e}")
                return None

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        print(f"⚡ [이화여자대학교] {target_date} 파싱 시도 중...")
        all_cafeterias = []
        
        # 요일 인덱스 계산 (0: 월, 1: 화, ..., 6: 일)
        target_weekday = target_date.weekday()

        for caf in self.CAFETERIAS:
            html = await self.fetch_html(caf["no"], target_date)
            if not html: continue

            soup = BeautifulSoup(html, 'html.parser')
            menu_box = soup.select_one("ul.b-menu-box")
            if not menu_box: continue

            # 💡 [핵심 수정] 모든 요일 리스트(li) 중 target_date에 맞는 요일을 선택
            # 사진의 클래스명 b-menu-day mon, tue 등을 활용하거나 리스트 순서로 접근
            day_lis = menu_box.select("li.b-menu-day")
            if not day_lis or target_weekday >= len(day_lis):
                continue

            target_li = day_lis[target_weekday]
            daily_menus = []

            # 조식, 중식, 석식 div 탐색
            meal_divs = target_li.select("div[class*='b-menu-']")

            for div in meal_divs:
                title_p = div.select_one("p.m-title")
                menu_pre = div.select_one("pre")
                
                if not title_p or not menu_pre: continue

                meal_type_raw = title_p.get_text(strip=True)
                if "조식" in meal_type_raw: meal_type = "BREAKFAST"
                elif "중식" in meal_type_raw: meal_type = "LUNCH"
                elif "석식" in meal_type_raw: meal_type = "DINNER"
                else: continue

                menu_text = menu_pre.get_text(strip=True)
                if not menu_text or "등록된 식단이 없습니다" in menu_text:
                    continue

                # 메뉴 아이템 리스트화
                menu_items = [item.strip() for item in menu_text.split() if item.strip()]
                
                if menu_items:
                    daily_menus.append(MenuData(
                        meal_type=meal_type,
                        menu_items=menu_items,
                        date=target_date
                    ))

            if daily_menus:
                print(f"  ✅ {caf['name']}: {len(daily_menus)}개의 식단 수집 완료")
                all_cafeterias.append(CafeteriaData(name=caf["name"], menus=daily_menus))
            
            await asyncio.sleep(0.3) # 서버 부하 방지

        if not all_cafeterias: return None

        return SchoolData(
            school_name=self.school_name,
            school_region=self.school_region,
            cafeterias=all_cafeterias
        )