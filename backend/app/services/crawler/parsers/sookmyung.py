import os
import json
import time
import re
import google.generativeai as genai
from PIL import Image
from datetime import date
from typing import Optional
from app.core.config import settings
from app.services.crawler.scrapers import BaseScraper
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class SookmyungScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            school_name="숙명여자대학교",
            school_region="서울",
            url=""
        )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = None

    def _get_active_model_name(self):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for m_name in available_models:
                if "gemini-2.0-flash-exp" in m_name: return m_name
            return "models/gemini-2.0-flash-exp"
        except:
            return "models/gemini-2.0-flash-exp"

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        # 모델 초기화
        if not self.model:
            model_name = self._get_active_model_name()
            self.model = genai.GenerativeModel(model_name)

        image_path = None
        for path in [".", "assets/images", "../assets/images"]:
            for ext in ["jpg", "jpeg", "png"]:
                temp = os.path.join(path, f"sookmyung.{ext}")
                if os.path.exists(temp):
                    image_path = temp; break
            if image_path: break

        if not image_path: return None

        # 🔴 [핵심] 재시도 로직 시작
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"⚡ [숙명여자대학교] {target_date} 파싱 시도 중... (시도 {attempt + 1}/{max_retries})")
                img = Image.open(image_path)
                prompt = f"숙명여자대학교 학식 메뉴판 이미지에서 {target_date.strftime('%Y-%m-%d')} 메뉴를 JSON으로 추출해줘. 없으면 [] 반환."
                
                response = self.model.generate_content([prompt, img])
                
                # 성공 시 데이터 처리
                text = response.text.strip()
                if "```json" in text: text = text.split("```json")[1].split("```")[0]
                elif "```" in text: text = text.split("```")[1].split("```")[0]
                data = json.loads(text)
                
                # (데이터 가공 로직 생략 - 이전과 동일)
                # ... [기존 가공 로직] ...
                print(f"  ✅ {target_date} 파싱 성공!")
                # 가공된 SchoolData 반환 (여기서는 생략, 기존 코드의 return 부분 사용)
                return self._process_data(data, target_date) 

            except Exception as e:
                error_msg = str(e)
                
                # 🔴 429 에러(할당량 초과) 발생 시
                if "429" in error_msg:
                    # 에러 메시지에서 "Please retry in X.Xs" 부분을 찾습니다.
                    wait_time = 60 # 기본값 60초
                    match = re.search(r"retry in ([\d\.]+)s", error_msg)
                    if match:
                        wait_time = float(match.group(1)) + 2 # 안전하게 2초 더 쉼
                    
                    print(f"  🛑 할당량 초과! 구글 요청에 따라 {wait_time}초 대기 후 재시도합니다...")
                    time.sleep(wait_time)
                    continue # 다음 시도로 넘어감
                
                else:
                    print(f"  ❌ 에러 발생: {e}")
                    break # 다른 종류의 에러는 중단
        
        return None

    def _process_data(self, data, target_date):
        # 기존에 작성했던 데이터 가공 로직을 이 함수로 분리해서 넣으시면 코드가 깔끔해집니다.
        caf_dict = {}
        for item in data:
            raw = item.get("cafeteria", "식당")
            name = "순헌관" if any(x in raw for x in ["본우리", "순헌"]) else "명신관"
            if name not in caf_dict:
                caf_dict[name] = CafeteriaData(name=name, menus=[])
            caf_dict[name].menus.append(MenuData(
                meal_type=item.get("meal_type", "LUNCH").upper(),
                menu_items=[m.strip() for m in str(item.get("menu", "")).split(",") if m.strip()],
                date=target_date
            ))
        return SchoolData(school_name=self.school_name, school_region=self.school_region, cafeterias=list(caf_dict.values()))