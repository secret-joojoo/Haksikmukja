import re
from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import httpx
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class KaisteastScraper(BaseScraper):
    # 동맛골 전용 Scraper니까 얘만 넣으면 돼!
    CAFETERIAS = [
        {"code": "east1", "name": "동맛골"}, 
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
        
        print(f"  ➳ [동맛골] 접속 시도: {target_url}")

        try:
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=10.0) as client:
                response = await client.get(target_url)
                if response.status_code == 200:
                    response.encoding = "utf-8"
                    return response.text
                return None
        except Exception as e:
            print(f"     ❌ 에러 발생: {cafeteria_code} ({str(e)}) -> Skip")
            return None

    def _clean_menu_item(self, text: str) -> str:
        text = re.sub(r'\([0-9,\s]+\)', '', text) # 알레르기(괄호 숫자) 제거
        text = re.sub(r'\[.*?\]', '', text)       # 대괄호 정보 제거
        text = text.replace('"', '').strip()      # 따옴표 제거

        # 공지사항 키워드 필터링
        ignore_keywords = [
            "운영", "종료", "안내", "식권", "감사합니다", "부탁", "소지", 
            "반출", "외부", "금지", "품절", "kcal", "원산지", "게시", 
            "주간", "변경"
        ]
        
        if any(keyword in text for keyword in ignore_keywords):
            return ""
            
        return text

    def _clean_text_lines(self, element) -> List[str]:
        if not element: return []
        text = element.get_text(separator="\n")
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _parse_generic_section(self, lines: List[str], base_meal_type: str, target_date: date) -> List[MenuData]:
        """
        동맛골 전용 파서: 헤더(< > 또는 ★)를 기준으로 섹션을 나누고,
        알 수 없는 헤더(Self-Bar 등)는 과감하게 스킵합니다.
        """
        menus = []
        current_suffix = ""
        current_items = []
        
        # 기본값: True (헤더를 만나기 전까지 나오는 잡다한 텍스트 무시)
        skip_mode = True 

        # 한글 Suffix 매핑
        header_map = {
            "한식": " 한식코너",
            "아메리칸": " 아메리칸",
            "샐러드": " 샐러드",
            "일품": " 일품코너",
            "Cafeteria": " Cafeteria",
            "동원홈푸드": "IGNORE", # 공지사항 무시
            # "Self-Bar": "IGNORE" # 리스트에 없으면 자동 무시됨
        }

        for line in lines:
            clean_line = line.strip().replace('"', '')
            # 헤더인지 판별 (<...> or ★...★)
            is_header_line = (clean_line.startswith("<") and clean_line.endswith(">")) or \
                             (clean_line.startswith("★") and clean_line.endswith("★"))

            if is_header_line:
                # 1. 이전 섹션 저장 (수집 모드였을 경우에만)
                if current_items and not skip_mode:
                    full_meal_type = f"{base_meal_type}{current_suffix}"
                    menus.append(MenuData(meal_type=full_meal_type, menu_items=current_items, date=target_date))
                
                # 2. 상태 초기화 (일단 무시 모드로 시작)
                current_items = []
                current_suffix = ""
                skip_mode = True 

                # 3. 아는 헤더인지 확인
                for key, suffix in header_map.items():
                    if key in clean_line:
                        if suffix != "IGNORE":
                            skip_mode = False # 아는 놈이다! 수집 시작
                            current_suffix = suffix
                        else:
                            skip_mode = True  # 명시적 무시 (동원홈푸드 등)
                        break
                continue # 헤더 줄 자체는 저장 안 함

            # 내용 수집 (무시 모드가 아닐 때만)
            if not skip_mode:
                cleaned = self._clean_menu_item(line)
                if cleaned and len(cleaned) > 1:
                    current_items.append(cleaned)

        # 마지막 섹션 저장
        if current_items and not skip_mode:
            full_meal_type = f"{base_meal_type}{current_suffix}"
            menus.append(MenuData(meal_type=full_meal_type, menu_items=current_items, date=target_date))

        return menus

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        print(f"⚡ KAIST 동맛골(East) 파싱 시작 ({target_date})")
        
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
                daily_menus.extend(self._parse_generic_section(bf_lines, "조식", target_date))

            # [1] 중식
            lunch_lines = self._clean_text_lines(tds[1])
            if lunch_lines:
                daily_menus.extend(self._parse_generic_section(lunch_lines, "중식", target_date))

            # [2] 석식
            dn_lines = self._clean_text_lines(tds[2])
            if dn_lines:
                daily_menus.extend(self._parse_generic_section(dn_lines, "석식", target_date))

            if daily_menus:
                print(f"  ✅ {name} 데이터 수집 완료 ({len(daily_menus)}개 코너)")
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