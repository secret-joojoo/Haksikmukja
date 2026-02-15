import sys
# Python 3.13 호환성 패치
if "cgi" not in sys.modules:
    import html
    from unittest.mock import MagicMock
    mock_cgi = MagicMock()
    def parse_header(line):
        parts = line.split(';')
        key = parts[0].strip()
        pdict = {}
        for part in parts[1:]:
            if '=' in part:
                name, value = part.split('=', 1)
                name = name.strip()
                value = value.strip().strip('"')
                pdict[name] = value
        return key, pdict
    mock_cgi.parse_header = parse_header
    mock_cgi.escape = html.escape
    sys.modules["cgi"] = mock_cgi

from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import re
import httpx
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

# =============================================================================
# 1. 서울시립대 공통 부모 클래스
# =============================================================================
class UosCafeteriaBase:
    def __init__(self, name: str, menuid: str, rstcde: str = None):
        self.name = name
        self.menuid = menuid
        self.rstcde = rstcde 
        self.base_url = "https://www.uos.ac.kr/food/placeList.do"

    async def fetch_html(self, target_date: date) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        formatted_date = target_date.strftime("%Y%m%d")
        target_url = f"{self.base_url}?search_date={formatted_date}&menuid={self.menuid}"
        if self.rstcde:
            target_url += f"&rstcde={self.rstcde}"
        
        try:
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=10.0) as client:
                response = await client.get(target_url)
                if response.status_code == 200:
                    response.encoding = "utf-8"
                    return response.text
                return None
        except Exception as e:
            print(f"     ❌ 에러 발생: {self.name} ({str(e)}) -> Skip")
            return None

    def _clean_menu_item(self, text: str) -> str:
        """기본 정리 로직 (가격 삭제 포함)"""
        text = re.sub(r'\([0-9,]+원\)', '', text)
        text = text.replace('"', '').strip()
        
        ignore_keywords = [
            "kcal", "g/", "원산지", "돈육", "계육", "우육", "국내산", "호주산", "브라질산", 
            "중국산", "식재료", "조달", "내부", "사정", "변동", "토핑", "코너", "운영시간",
            "식단", "제공", "마감", "입장", "예약", "신청", "이메일", "접수", "회신", "인원"
        ]
        
        if re.search(r'\d{1,2}:\d{2}~\d{1,2}:\d{2}', text): return ""
        if "원" in text and re.search(r'[0-9,]', text): return "" 
        if not re.search(r'[가-힣]', text): return "" 

        if any(keyword in text for keyword in ignore_keywords): return "" 
        if len(text) <= 1: return ""
        return text.strip()

    def _clean_text_lines(self, element) -> List[str]:
        if not element: return []
        text = element.get_text(separator="\n")
        return [line.strip() for line in text.split("\n") if line.strip()]

    async def parse(self, target_date: date) -> Optional[CafeteriaData]:
        html = await self.fetch_html(target_date)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        
        table = soup.find("table")
        if not table: return None
        tbody = table.find("tbody")
        if not tbody: return None
        tr = tbody.find("tr")
        if not tr: return None
        tds = tr.find_all("td")
        if len(tds) < 3: return None

        menus = self._extract_menus(tds, target_date)
        if menus:
            return CafeteriaData(name=self.name, menus=menus)
        return None
    
    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        raise NotImplementedError

    def _parse_column(self, lines: List[str], target_date: date, keywords_map: dict, default_category: str = None) -> List[MenuData]:
        extracted_menus = []
        current_category = default_category
        current_items = []

        for line in lines:
            is_header = False
            for key, category_code in keywords_map.items():
                if key in line:
                    if current_category and current_items:
                        extracted_menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))
                    current_category = category_code
                    current_items = []
                    is_header = True
                    break
            
            if is_header: continue

            if current_category:
                cleaned = self._clean_menu_item(line)
                if cleaned:
                    current_items.append(cleaned)

        if current_category and current_items:
            extracted_menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))

        return extracted_menus


# =============================================================================
# 2. 식당별 구현체
# =============================================================================

class StudentHall1Parser(UosCafeteriaBase):
    def __init__(self):
        super().__init__("학생회관 1층", "2000005006002000000")

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        menus.extend(self._parse_column(self._clean_text_lines(tds[0]), target_date, {"C코너": "BREAKFAST_C"}))
        menus.extend(self._parse_column(self._clean_text_lines(tds[1]), target_date, {"A코너": "LUNCH_A", "C코너": "LUNCH_C", "D코너": "LUNCH_D"}))
        menus.extend(self._parse_column(self._clean_text_lines(tds[2]), target_date, {"C코너": "DINNER_C", "D코너": "DINNER_D"}))
        return menus

class IrumLoungeParser(UosCafeteriaBase):
    def __init__(self):
        super().__init__("이룸라운지", "2000005006002000000", rstcde="010")

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        menus.extend(self._parse_column(self._clean_text_lines(tds[1]), target_date, {"일반식": "LUNCH", "고급식A": "PREMIUM_A", "고급식B": "PREMIUM_B"}))
        menus.extend(self._parse_column(self._clean_text_lines(tds[2]), target_date, {"일반식": "DINNER", "고급식A": "IGNORE", "고급식B": "IGNORE"}))
        return menus

class WesternRestaurantParser(UosCafeteriaBase):
    def __init__(self):
        super().__init__("양식당", "2000005006002000000", rstcde="030")

    def _clean_menu_item(self, text: str) -> str:
        """양식당 전용 (가격 보존)"""
        text = text.replace('"', '').strip()
        
        ignore_keywords = [
            "kcal", "g/", "원산지", "돈육", "계육", "우육", "국내산", "호주산", "브라질산", 
            "중국산", "식재료", "조달", "내부", "사정", "변동", "토핑", "코너", "운영시간",
            "식단", "제공", "마감", "입장", "예약", "신청", "이메일", "접수", "회신", "인원",
            "면류", "밥류", "조정", "간격"
        ]
        
        if re.search(r'\d{1,2}:\d{2}~\d{1,2}:\d{2}', text): return ""
        if re.match(r'^\([가-힣]+\)$', text): return "" # (양식류) 같은 헤더 제거

        # 한글 없고 가격도 없으면 삭제 (순수 영어 메뉴명)
        if not re.search(r'[가-힣]', text):
            if not ("원" in text and re.search(r'[0-9,]', text)):
                return ""

        if any(keyword in text for keyword in ignore_keywords): return "" 
        if len(text) <= 1: return ""
        return text.strip()

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        menus.extend(self._parse_column(self._clean_text_lines(tds[1]), target_date, {}, default_category="LUNCH"))
        return menus

class NaturalScienceHallParser(UosCafeteriaBase):
    def __init__(self):
        # 자연과학관: rstcde=040
        super().__init__("자연과학관", "2000005006002000000", rstcde="040")

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        
        # td[0]: 조식 정보 칸이지만 메뉴 없음 (운영시간 텍스트만 있음) -> 무시
        
        # [1] 중식 (tds[1]) - 기본 LUNCH
        menus.extend(self._parse_column(
            self._clean_text_lines(tds[1]), 
            target_date, 
            {}, 
            default_category="LUNCH"
        ))

        # [2] 석식 (tds[2]) - 기본 DINNER
        menus.extend(self._parse_column(
            self._clean_text_lines(tds[2]), 
            target_date, 
            {}, 
            default_category="DINNER"
        ))

        return menus


# =============================================================================
# 3. 메인 스크래퍼
# =============================================================================
class UosScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            school_name="서울시립대학교",
            school_region="서울",
            url=""
        )
        self.parsers = [
            StudentHall1Parser(),
            IrumLoungeParser(),
            WesternRestaurantParser(),
            NaturalScienceHallParser(), # 자연과학관 추가
        ]

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        print(f"⚡ 서울시립대 파싱 시작 ({target_date})")
        
        all_cafeterias = []

        for parser in self.parsers:
            caf_data = await parser.parse(target_date)
            if caf_data:
                print(f"  ✅ {caf_data.name} 데이터 수집 완료")
                all_cafeterias.append(caf_data)
            else:
                pass 

        if not all_cafeterias:
            return None

        return SchoolData(
            school_name=self.school_name,
            school_region=self.school_region,
            cafeterias=all_cafeterias
        )