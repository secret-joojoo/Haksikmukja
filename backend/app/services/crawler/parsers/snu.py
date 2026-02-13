from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional
import re
import httpx
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class SnuScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            school_name="서울대학교",
            school_region="서울",
            url="https://snuco.snu.ac.kr/foodmenu/"
        )

    async def fetch_html(self, target_date: date):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        formatted_date = target_date.strftime("%Y-%m-%d")
        target_url = f"{self.url}?date={formatted_date}"
        
        print(f"  ➳ 접속 시도: {self.school_name} ({target_url})")

        try:
            async with httpx.AsyncClient(verify=False, headers=headers, timeout=10.0) as client:
                response = await client.get(target_url)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"     ⚠️ 접속 실패 (Status: {response.status_code}) -> Skip")
                    return None
        except Exception as e:
            print(f"     ❌ 에러 발생: {str(e)} -> Skip")
            return None

    def _clean_menu_item(self, text: str) -> str:
        """메뉴 텍스트에서 특수문자, 공지사항 등을 제거하여 깔끔하게 만듦"""
        if not text: return ""

        # ※ 기호가 있는 라인은 아예 무시
        if "※" in text:
            return ""

        # 파싱 찌꺼기 강력 제거
        text = text.strip()
        if text.startswith(">") or text.endswith("코너>") or text in ["식 메뉴", "메뉴"]:
            return ""

        # 가격만 덩그러니 있는 줄 제거
        if re.match(r'^\s*[\d,]+\s*원?\s*$', text):
            return ""

        # 특수문자 정리
        text = re.sub(r'<([^>]+)>', r'[\1]', text)
        text = re.sub(r'\([#]\)', '', text)
        
        # 불필요한 공지 키워드 삭제
        ignore_keywords = [
            "제공", "운영", "식단", "참고", "안내", "문의", "품절", 
            "배식", "kcal", "원산지", "마감", "종료", "시간", "부탁"
        ]
        
        if any(keyword in text for keyword in ignore_keywords):
            return ""
            
        return text.strip()

    def _parse_menu_column(self, element, meal_type: str, target_date: date) -> List[MenuData]:
        """
        TD 요소를 파싱하여 MenuData 리스트를 반환함.
        """
        if not element: return []
        
        text = element.get_text(separator="\n")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        generated_menus = []
        current_meal_type = meal_type # 기본값 (예: LUNCH)
        current_items = []
        
        # [IGNORE_MODE] 활성화 시, 다음 헤더가 나올 때까지 모든 줄 무시
        ignore_mode = False 
        
        for line in lines:
            if "※" in line: continue

            # === 코너 및 메뉴 감지 로직 ===
            new_suffix = None
            content_to_add = line
            add_this_line = True # 기본적으로 내용은 메뉴에 추가함
            
            # 1. 뷔페 감지 (302동 등)
            if "뷔페" in line:
                new_suffix = "_BUFFET"
                add_this_line = False 

            # 2. 천원의 아침밥 (301동)
            elif "천원의" in line and "아침" in line:
                new_suffix = "_1000" 
                add_this_line = False

            # 3. 교직원 식당 (301동)
            elif "교직원" in line:
                new_suffix = "_FACULTY"
                add_this_line = False

            # 4. [식사] -> 기본 메뉴로 복귀 (301동)
            elif "[식사]" in line or "<식사>" in line:
                new_suffix = "_RESET" # 그냥 LUNCH/DINNER로 돌아감
                add_this_line = False

            # 5. [강화됨] Take-out / 카페 감지 (대소문자 무시, 하이픈 유연하게)
            # Take-out, Takeout, Take out, Cafe, 카페 모두 잡음
            elif re.search(r'Take\s*-?\s*out|테이크\s*아웃|카페|Cafe', line, re.IGNORECASE):
                new_suffix = "_TAKEOUT" 
                add_this_line = False   # 헤더 텍스트는 메뉴 목록에서 뺌

            # 6. A/B/C 코너 감지
            elif re.search(r'[\[\<]?\s*A코너\s*[\]\>]?', line):
                new_suffix = "_A"
                content_to_add = re.sub(r'[\[\<]?\s*A코너\s*[\]\>]?[\s:]*', '', line)
            elif re.search(r'[\[\<]?\s*B코너\s*[\]\>]?', line):
                new_suffix = "_B"
                content_to_add = re.sub(r'[\[\<]?\s*B코너\s*[\]\>]?[\s:]*', '', line)
            elif re.search(r'[\[\<]?\s*C코너\s*[\]\>]?', line):
                new_suffix = "_C"
                content_to_add = re.sub(r'[\[\<]?\s*C코너\s*[\]\>]?[\s:]*', '', line)
            
            # 7. 셀프/주문식 감지
            elif "셀프" in line: 
                new_suffix = "_SELF"
                content_to_add = re.sub(r'[\[\<]?\s*(셀프코너|셀프)\s*[\]\>]?[\s:]*', '', line)
            elif "주문" in line: 
                if any(bad in line for bad in ["마감", "시간", "종료"]): 
                    continue
                new_suffix = "_ORDER"
                content_to_add = re.sub(r'[\[\<]?\s*(주문식\s*메뉴|주문식|주문)\s*[\]\>]?[\s:]*', '', line)

            # === 상태 변경 처리 ===
            if new_suffix:
                # 이전까지 모은 메뉴가 있다면 저장 (IGNORE 모드가 아니었을 때만)
                if current_items and not ignore_mode:
                    generated_menus.append(MenuData(meal_type=current_meal_type, menu_items=current_items, date=target_date))
                
                # 상태 업데이트
                if new_suffix == "_IGNORE":
                    ignore_mode = True
                    current_items = []
                elif new_suffix == "_RESET":
                    ignore_mode = False
                    current_meal_type = meal_type # 기본 타입으로 복귀
                    current_items = []
                else:
                    ignore_mode = False
                    current_meal_type = f"{meal_type}{new_suffix}"
                    current_items = []
                
                # 이 줄의 내용을 추가해야 한다면 추가
                if add_this_line and not ignore_mode:
                    cleaned = self._clean_menu_item(content_to_add)
                    if cleaned and len(cleaned) > 1:
                        current_items.append(cleaned)
                continue

            # 일반 메뉴 추가 (IGNORE 모드가 아닐 때만)
            if not ignore_mode:
                cleaned = self._clean_menu_item(line)
                if cleaned and len(cleaned) > 1:
                    current_items.append(cleaned)
                
        # 반복문 종료 후 남은 메뉴 저장
        if current_items and not ignore_mode:
            generated_menus.append(MenuData(meal_type=current_meal_type, menu_items=current_items, date=target_date))
            
        return generated_menus

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        print(f"⚡ 서울대학교 식단 파싱 시작 ({target_date})")
        html = await self.fetch_html(target_date)
        if not html: return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = soup.find_all("table")
        target_table = None
        
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            
            if not headers:
                first_tr = table.find("tr")
                if first_tr:
                    headers = [td.get_text(strip=True) for td in first_tr.find_all("td")]
            
            if headers:
                print(f"    🔍 테이블 헤더 발견: {headers}")

            menu_keywords = ["조식", "중식", "석식", "아침", "점심", "저녁"]
            if any(k in h for h in headers for k in menu_keywords):
                target_table = table
                break
        
        if not target_table:
            print("  ⚠️ 식단 테이블을 찾을 수 없습니다. (헤더 매칭 실패)")
            return None
            
        tbody = target_table.find("tbody")
        if not tbody: 
            tbody = target_table
        
        rows = tbody.find_all("tr")
        all_cafeterias = []
        
        target_mappings = [
            (["학생회관식당"], "학생회관식당"),
            (["자하연식당 3층"], "자하연식당 3층"),
            (["자하연식당 2층"], "자하연식당 2층"),
            (["예술계식당"], "예술계식당"),
            (["두레미담"], "두레미담"),
            (["동원관식당"], "동원관식당"),
            (["기숙사식당"], "기숙사식당"),
            (["3식당"], "3식당"),
            (["302동식당"], "302동식당"),
            (["301동식당"], "301동식당")
        ]
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4: continue
            
            caf_name_raw = cols[0].get_text(strip=True)
            
            matched_name = None
            for keywords, save_name in target_mappings:
                if all(k in caf_name_raw for k in keywords):
                    matched_name = save_name
                    break
            
            if not matched_name:
                continue

            daily_menus = []
            
            bf_menus = self._parse_menu_column(cols[1], "BREAKFAST", target_date)
            daily_menus.extend(bf_menus)
            
            lc_menus = self._parse_menu_column(cols[2], "LUNCH", target_date)
            daily_menus.extend(lc_menus)
            
            dn_menus = self._parse_menu_column(cols[3], "DINNER", target_date)
            daily_menus.extend(dn_menus)
            
            if daily_menus:
                print(f"  ✅ {matched_name} 데이터 수집 완료 ({len(daily_menus)}개 메뉴 그룹)")
                all_cafeterias.append(CafeteriaData(name=matched_name, menus=daily_menus))

        if not all_cafeterias:
            print("  ❌ 수집된 식당 데이터가 없습니다.")
            return None

        return SchoolData(
            school_name=self.school_name,
            school_region=self.school_region,
            cafeterias=all_cafeterias
        )