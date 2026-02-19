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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.uos.ac.kr/food/placeList.do",
            "Origin": "https://www.uos.ac.kr"
        }
        formatted_date = target_date.strftime("%Y%m%d")
        
        # URL 파라미터 (식당 구분용 rstcde는 URL에 붙임)
        params = {}
        if self.rstcde:
            params["rstcde"] = self.rstcde
            
        # Body 데이터 (날짜와 메뉴ID는 POST Body로 전송)
        data = {
            "search_date": formatted_date,
            "menuid": self.menuid,
        }
        
        try:
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=10.0, follow_redirects=True) as client:
                response = await client.post(self.base_url, params=params, data=data)
                
                if response.status_code == 200:
                    response.encoding = "utf-8"
                    if len(response.text) < 1000:
                        print(f"     ⚠️ {self.name}: 응답이 너무 짧음 ({len(response.text)} bytes)")
                    return response.text
                else:
                    print(f"     ⚠️ {self.name}: 상태 코드 이상 ({response.status_code})")
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
            "식단", "제공", "마감", "입장", "예약", "신청", "이메일", "접수", "회신", "인원",
            "주간별", "미운영"
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
        
        day_div = soup.find("div", id="day")
        if not day_div:
            return None
            
        table = day_div.find("table")
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
                    if current_category and current_items and current_category != "IGNORE":
                        extracted_menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))
                    
                    current_category = category_code
                    current_items = []
                    is_header = True
                    break
            
            if is_header: continue

            if current_category and current_category != "IGNORE":
                cleaned = self._clean_menu_item(line)
                if cleaned:
                    current_items.append(cleaned)

        if current_category and current_items and current_category != "IGNORE":
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

    def _preprocess_plus_menu(self, lines: List[str]) -> List[str]:
        """
        '플러스 메뉴' 라인을 찾아서 쉼표로 분리하고, 별도의 헤더를 추가합니다.
        """
        processed = []
        for line in lines:
            if "플러스 메뉴" in line:
                content = re.sub(r'^\s*[\*]*\s*플러스\s*메뉴\s*[:]*\s*', '', line)
                processed.append("플러스 메뉴")
                items = [item.strip() for item in content.split(',') if item.strip()]
                processed.extend(items)
            else:
                processed.append(line)
        return processed

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        
        common_ignore = {
            "고급식": "IGNORE",
            "고급식A": "IGNORE",
            "고급식B": "IGNORE",
        }
        
        # [1] 중식
        lunch_lines = self._clean_text_lines(tds[1])
        lunch_lines = self._preprocess_plus_menu(lunch_lines) 
        lunch_map = common_ignore.copy()
        lunch_map["일반식"] = "LUNCH"
        lunch_map["플러스 메뉴"] = "LUNCH_PLUS"
        menus.extend(self._parse_column(lunch_lines, target_date, lunch_map))

        # [2] 석식
        dinner_lines = self._clean_text_lines(tds[2])
        dinner_lines = self._preprocess_plus_menu(dinner_lines) 
        dinner_map = common_ignore.copy()
        dinner_map["일반식"] = "DINNER"
        dinner_map["플러스 메뉴"] = "DINNER_PLUS"
        menus.extend(self._parse_column(dinner_lines, target_date, dinner_map))
        
        return menus

class WesternRestaurantParser(UosCafeteriaBase):
    def __init__(self):
        super().__init__("양식당", "2000005006002000000", rstcde="030")

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        # 양식당은 구조가 독특해서 별도 파싱 로직 사용
        # 형식: [한글 메뉴명] -> [영어(생략가능)] -> [가격]
        
        lines = self._clean_text_lines(tds[1]) # 중식만 운영
        menu_items = []
        current_menu_name = None
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 1. 시간 패턴이나 불필요한 라인 무시
            if re.search(r'\d{1,2}:\d{2}', line): continue
            
            # 2. 카테고리 패턴 무시 (예: (양식류), (덮밥류))
            if line.startswith('(') and line.endswith(')'): continue
            
            # 3. 가격 패턴 확인 (숫자와 '원'이 포함된 경우)
            if re.search(r'^\d{1,3}(,\d{3})*원', line):
                if current_menu_name:
                    # 가격을 찾으면 직전에 찾은 메뉴명과 합침
                    menu_items.append(f"{current_menu_name}: {line}")
                    current_menu_name = None
            else:
                # 4. 메뉴명 후보 찾기
                # 한글이 포함되어 있어야 유효한 메뉴명으로 간주 (영어 설명 제외)
                # '탄산음료(Soda)' 같이 한글+영어가 섞인 경우도 있으니 한글 유무로 판단
                if re.search(r'[가-힣]', line):
                    current_menu_name = line
                    
        if not menu_items:
            return []

        return [MenuData(meal_type="LUNCH", menu_items=menu_items, date=target_date)]

class NaturalScienceHallParser(UosCafeteriaBase):
    def __init__(self):
        super().__init__("자연과학관", "2000005006002000000", rstcde="040")

    def _extract_menus(self, tds, target_date: date) -> List[MenuData]:
        menus = []
        menus.extend(self._parse_column(self._clean_text_lines(tds[1]), target_date, {}, default_category="LUNCH"))
        menus.extend(self._parse_column(self._clean_text_lines(tds[2]), target_date, {}, default_category="DINNER"))
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
            NaturalScienceHallParser(),
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