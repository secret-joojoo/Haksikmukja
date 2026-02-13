from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import httpx
import re
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class CnuScraper(BaseScraper):
    # 실제 식당 이름 리스트 (인덱스 0은 제1학생회관이지만, 데이터는 1번부터 존재)
    CAFETERIA_NAMES = ["제1학생회관", "제2학생회관", "제3학생회관", "제4학생회관", "생활과학대학"]

    def __init__(self):
        super().__init__(
            school_name="충남대학교",
            school_region="대전",
            url="https://mobileadmin.cnu.ac.kr/food/index.jsp"
        )

    async def fetch_html(self, target_date: date):
        formatted_date = target_date.strftime("%Y.%m.%d")
        target_url = f"{self.url}?searchYmd={formatted_date}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://mobileadmin.cnu.ac.kr/food/index.jsp"
        }

        async with httpx.AsyncClient(verify=False, headers=headers, timeout=20.0) as client:
            try:
                response = await client.get(target_url)
                return response.text if response.status_code == 200 else None
            except Exception as e:
                print(f"❌ [충남대학교] 접속 에러: {e}")
                return None

    def _extract_menu_items(self, td) -> List[str]:
        if not td: return []
        p_tag = td.select_one("p")
        if not p_tag: return []
        
        text = p_tag.get_text(separator="\n", strip=True)
        items = [re.sub(r'\(.*\)', '', line).strip() for line in text.split("\n") if line.strip()]
        return [i for i in items if i and "운영안함" not in i and "운영중단" not in i]

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        html = await self.fetch_html(target_date)
        if not html: return None

        soup = BeautifulSoup(html, 'html.parser')
        table = soup.select_one("table.menu-tbl")
        if not table: return None

        caf_data_map = {name: [] for name in self.CAFETERIA_NAMES}
        rows = table.select("tbody tr")
        
        # 💡 [초엘리트 분석 결과] 
        # 제1학생회관 칸은 rowspan 때문에 모든 행에서 '앞 칸'을 잡아먹고 있음.
        # 따라서 모든 행에서 식당 데이터는 실제 인덱스보다 '앞으로 한 칸'씩 당겨짐.
        for idx, row in enumerate(rows):
            if idx in [0, 1]: meal_type = "BREAKFAST"
            elif idx in [2, 3]: meal_type = "LUNCH"
            elif idx in [4, 5]: meal_type = "DINNER"
            else: continue

            tds = row.find_all("td", recursive=False)
            
            # [보정 로직]
            # 1. '직원' 행(idx 0, 2, 4): [구분, 대상, (제1은 병합됨), 제2, 제3, 제4, 생과대] 순서
            #    즉, tds[2]가 제2학생회관, tds[5]가 생활과학대학임.
            # 2. '학생' 행(idx 1, 3, 5): [대상, (제1은 병합됨), 제2, 제3, 제4, 생과대] 순서
            #    즉, tds[1]이 제2학생회관, tds[4]가 생활과학대학임.
            
            base_offset = 2 if idx % 2 == 0 else 1
            
            # 제2학생회관(index 1)부터 생활과학대학(index 4)까지 수집
            for caf_idx in range(1, 5): 
                td_pos = base_offset + (caf_idx - 1)
                
                if td_pos < len(tds):
                    menu_items = self._extract_menu_items(tds[td_pos])
                    if menu_items:
                        caf_name = self.CAFETERIA_NAMES[caf_idx]
                        caf_data_map[caf_name].append(MenuData(
                            meal_type=meal_type,
                            menu_items=menu_items,
                            date=target_date
                        ))

        all_cafeterias = [
            CafeteriaData(name=name, menus=menus) 
            for name, menus in caf_data_map.items() if menus
        ]

        if not all_cafeterias: return None

        return SchoolData(
            school_name=self.school_name,
            school_region=self.school_region,
            cafeterias=all_cafeterias
        )