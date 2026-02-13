# --- [긴급 패치] Python 3.13 호환성 문제 해결 (httpx 구버전용) ---
import sys
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
# -------------------------------------------------------------

from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import re
import httpx
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class KaistScraper(BaseScraper):
    # 크롤링할 식당 목록 정의 (코드: 이름)
    CAFETERIAS = [
        {"code": "fclt", "name": "카이마루"},
        {"code": "west", "name": "서맛골"},
        {"code": "emp", "name": "교수회관"},
    ]

    def __init__(self):
        super().__init__(
            school_name="KAIST",
            school_region="대전",
            url="https://www.kaist.ac.kr/kr/html/campus/053001.html" 
        )

    async def fetch_html(self, cafeteria_code: str, target_date: date):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        formatted_date = target_date.strftime("%Y-%m-%d")
        target_url = f"{self.url}?dvs_cd={cafeteria_code}&stt_dt={formatted_date}"
        
        print(f"  ➳ 접속 시도: {cafeteria_code} ({target_url})")

        # 🔴 [수정] 예외 처리 강화: 사이트가 죽었거나 응답이 없으면 쿨하게 스킵!
        try:
            # timeout=10.0 추가: 10초 동안 응답 없으면 그냥 포기해 (성격 급해서 못 기다려)
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=10.0) as client:
                response = await client.get(target_url)
                
                # 상태 코드가 200(성공)일 때만 데이터 반환
                if response.status_code == 200:
                    response.encoding = "utf-8"
                    return response.text
                else:
                    # 404(없음)나 500(서버 에러) 같은 게 뜨면 경고만 남기고 None 반환
                    print(f"     ⚠️ 접속 실패 (Status: {response.status_code}) -> Skip")
                    return None

        except Exception as e:
            # 인터넷 연결이 없거나 타임아웃 등 모든 에러를 여기서 잡아냄
            print(f"     ❌ 에러 발생: {cafeteria_code} ({str(e)}) -> Skip")
            return None

    def _clean_menu_item(self, text: str) -> str:
        """메뉴 이름 정리 및 잡다한 공지사항 제거"""
        # 1. 괄호() 또는 대괄호[] 안에 포함된 가격/알레르기 정보 제거
        # 예: (1,5), [6,500원] -> 모두 제거
        text = re.sub(r'[\[\(][0-9.,원\s]+[\]\)]', '', text)
        
        # 3. [업데이트] 공지사항 키워드 필터링 (여기에 단어 추가하면 다 지워짐!)
        ignore_keywords = [
            "천원", "제공", "캠페인", "운영시간", "안녕하세요", 
            "학생증", "간식", "참고", "감사합니다", "부탁", "소지", "kcal"
        ]
        
        # 위 단어 중 하나라도 포함되어 있으면 빈 문자열 반환 (삭제)
        if any(keyword in text for keyword in ignore_keywords):
            return "" 
            
        return text

    def _clean_text_lines(self, element) -> List[str]:
        if not element: return []
        text = element.get_text(separator="\n")
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _parse_breakfast_detailed(self, lines: List[str], target_date: date) -> List[MenuData]:
        menus = []
        current_category = "BREAKFAST" # 기본값: 일반 조식
        current_items = []
        
        # 🔴 [핵심] 조식 키워드 분리
        keywords = {
            "천원의 아침밥": "BREAKFAST_1000", # 저장될 이름: BREAKFAST_1000
            "조식": "BREAKFAST"          # 저장될 이름: BREAKFAST (기본)
        }

        for line in lines:
            is_header = False
            for key, code in keywords.items():
                if key in line:
                    if current_items:
                        menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))
                    
                    current_category = code
                    current_items = []
                    is_header = True
                    break
            
            if not is_header:
                # "조식"이나 "천원의 아침밥" 같은 헤더 텍스트는 메뉴에 포함되면 안 됨
                cleaned = self._clean_menu_item(line)
                if cleaned and len(cleaned) > 1 and "원" not in cleaned:
                    current_items.append(cleaned)

        if current_items:
            menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))

        return menus


    def _parse_lunch_detailed(self, lines: List[str], target_date: date) -> List[MenuData]:
        menus = []
        current_category = "LUNCH" 
        current_items = []
        
        keywords = {
            "1층 자율배식": "LUNCH_1F",
            "2층 자율배식": "LUNCH_2F",
            "자율배식": "LUNCH",
            "A코너": "LUNCH_A",
            "B코너": "LUNCH_B",
            "일품": "LUNCH_SPECIAL",
            "교직원": "LUNCH_STAFF"
        }

        for line in lines:
            is_header = False
            for key, code in keywords.items():
                if key in line:
                    if current_items:
                        menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))
                    current_category = code
                    current_items = []
                    is_header = True
                    break
            
            if not is_header:
                cleaned = self._clean_menu_item(line)
                # 공지사항 필터링 후 내용이 남았고, '원' 같은 글자가 없어야 추가
                if cleaned and len(cleaned) > 1 and "원" not in cleaned:
                    current_items.append(cleaned)

        if current_items:
            menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))

        return menus

    def _parse_dinner_detailed(self, lines: List[str], target_date: date) -> List[MenuData]:
        menus = []
        current_category = "DINNER" # 기본은 그냥 저녁
        current_items = []
        
        # 🔴 [추가] 저녁 특식 키워드 정의
        keywords = {
            "일품": "석식 일품",
        }

        for line in lines:
            is_header = False
            for key, code in keywords.items():
                if key in line:
                    # 새로운 키워드가 나오면 지금까지 모은 걸 저장
                    if current_items:
                        menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))
                    
                    current_category = code # 카테고리 변경 (예: DINNER -> DINNER_SPECIAL)
                    current_items = []
                    is_header = True
                    break
            
            if not is_header:
                if "석식" in line: continue # "석식" 같은 헤더는 무시
                
                cleaned = self._clean_menu_item(line)
                # 내용이 있고 "원"이 포함되지 않은 메뉴만 추가
                if cleaned and len(cleaned) > 1 and "원" not in cleaned:
                    current_items.append(cleaned)

        # 마지막에 남은 메뉴들 저장
        if current_items:
            menus.append(MenuData(meal_type=current_category, menu_items=current_items, date=target_date))

        return menus

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        print(f"⚡ KAIST 전체 식당 파싱 시작 ({target_date})")
        
        all_cafeterias = []

        for caf_info in self.CAFETERIAS:
            code = caf_info["code"]
            name = caf_info["name"]

            html = await self.fetch_html(code, target_date)
            if not html: continue
            
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find("table", class_="table")
            if not table: continue
            tbody = table.find("tbody")
            if not tbody: continue
            tr = tbody.find("tr")
            if not tr: continue
            tds = tr.find_all("td")
            if len(tds) < 3: continue

            daily_menus = []

            # [0] 조식
            bf_lines = self._clean_text_lines(tds[0])
            if bf_lines:
                # 아까의 break 로직은 버리고, 상세 파싱 함수를 호출해!
                daily_menus.extend(self._parse_breakfast_detailed(bf_lines, target_date))

            # [1] 중식 (상세 파싱)
            lunch_lines = self._clean_text_lines(tds[1])
            if lunch_lines:
                daily_menus.extend(self._parse_lunch_detailed(lunch_lines, target_date))

            # [2] 석식
            dn_lines = self._clean_text_lines(tds[2])
            if dn_lines:
                # 단순 파싱 대신 상세 파싱 함수를 호출해서 특식을 분리해!
                daily_menus.extend(self._parse_dinner_detailed(dn_lines, target_date))

            if daily_menus:
                print(f"  ✅ {name} 데이터 수집 완료")
                all_cafeterias.append(CafeteriaData(name=name, menus=daily_menus))
            else:
                print(f"  ⚠️ {name} 데이터 없음")

        if not all_cafeterias:
            return None

        return SchoolData(
            school_name=self.school_name,
            school_region=self.school_region,
            cafeterias=all_cafeterias
        )