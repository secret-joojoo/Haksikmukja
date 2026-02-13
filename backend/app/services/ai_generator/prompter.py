from deep_translator import GoogleTranslator
from typing import List

class MenuPrompter:
    def __init__(self):
        self.translator = GoogleTranslator(source='ko', target='en')
        
        # [수정됨] '3D', 'Unreal Engine' 같은 단어 싹 뺐어!
        # 대신 'Food Photography'(음식 사진)라는 말을 강조해서 진짜 사진처럼 나오게 유도함.
        self.base_prompt = (
            "A high-quality 3D rendered isometric image of a stainless steel {meal_keywords} tray. "
            "The tray contains the following delicious Korean dishes: {menu_items}. "
            "The food is arranged neatly with exaggerated depth and volume. "
            
            # ✨ 마법의 단어들 (3D 툴 이름 추가)
            "Unreal Engine 5 render, Octane Render, Blender 3D, Ray Tracing, "
            "Volumetric lighting, Global Illumination, Ambient Occlusion, "
            "4k resolution, hyper-detailed, glossy textures, "
            
            # 배경을 단순하게 날려서 음식만 둥둥 떠 있는 느낌 (원하면 유지)
            "clean background, soft shadows, sharp focus, vivid colors. "
            
            # 🚫 2D 느낌 절대 사절 (부정 프롬프트)
            "(no flat, no 2D, no sketch, no drawing, no painting, no watermark, no text, no distorted food)"
        )

    async def translate_to_english(self, korean_menu_list: List[str]) -> str:
        try:
            joined_text = ", ".join(korean_menu_list)
            translated_text = self.translator.translate(joined_text)
            return translated_text
        except Exception as e:
            print(f"⚠️ 번역 실패: {e}")
            return ", ".join(korean_menu_list)

    def _detect_meal_keywords(self, meal_type_db: str) -> str:
        """복잡한 코드를 분석해서 적절한 영어 키워드를 반환"""
        upper_type = meal_type_db.upper()
        
        keywords = ["Korean School"] 

        if any(x in upper_type for x in ["BREAKFAST", "아침", "조식"]):
            keywords.append("Breakfast")
        elif any(x in upper_type for x in ["DINNER", "저녁", "석식"]):
            keywords.append("Dinner")
        else:
            keywords.append("Lunch")

        if any(x in upper_type for x in ["SPECIAL", "일품", "A코너", "A_CORNER"]):
            keywords.append("Special Set")
        elif any(x in upper_type for x in ["TAKEOUT", "테이크아웃", "CAFE", "PACKED"]):
            keywords.append("Packed Box") 
        elif any(x in upper_type for x in ["BUFFET", "뷔페"]):
            keywords.append("Buffet Plate")

        elif "샐러드" in upper_type or "SALAD" in upper_type:
            keywords.append("Fresh Salad Bowl, Healthy Diet")
        elif "아메리칸" in upper_type or "WESTERN" in upper_type:
            keywords.append("American Brunch, Toast, Sausage")
        elif "CAFETERIA" in upper_type:
            keywords.append("Cafeteria Tray, A la carte")
        elif "한식" in upper_type or "KOREAN" in upper_type:
            keywords.append("Traditional Korean Set")

        return " ".join(keywords)

    async def create_prompt(self, menu_items: List[str], meal_type_db: str) -> str:
        # 1. 메뉴 번역 (한글 -> 영어)
        english_menu = await self.translate_to_english(menu_items)
        
        # ---------------------------------------------------------
        # 💡 [솔루션] 메뉴 이름에 따라 '맛있는 묘사' 강제 주입!
        # AI가 모르는 한국 요리를 시각적으로 풀어서 설명해주는 코드야.
        # ---------------------------------------------------------
        visual_boosters = []
        full_menu_str = " ".join(menu_items) # 한국어 원문 확인용

        # 1) 매운 국물 요리 (빨간맛)
        if any(x in full_menu_str for x in ["매운탕", "찌개", "짬뽕", "육개장"]):
            visual_boosters.append("rich spicy red broth, boiling bubbles, tofu chunks, chili pepper garnish, steam rising")
        
        # 2) 맑은 국물 요리
        elif any(x in full_menu_str for x in ["국", "탕", "지리"]):
            visual_boosters.append("clear hot soup, steaming, chopped green onions, deep flavor")

        # 3) 고기 요리 (갈색맛)
        if any(x in full_menu_str for x in ["불고기", "갈비", "제육", "스테이크"]):
            visual_boosters.append("marinated grilled meat, sizzling, juicy, brown sauce, glossy texture")
            
        # 4) 밥 요리
        if any(x in full_menu_str for x in ["밥", "볶음밥", "덮밥"]):
            visual_boosters.append("fluffy white rice textures")

        # 묘사가 있으면 영어 메뉴 뒤에 콤마(,) 찍고 추가
        if visual_boosters:
            english_menu += ", " + ", ".join(visual_boosters)
        # ---------------------------------------------------------

        # 2. 키워드 추출 (기존 로직 유지)
        meal_keywords = self._detect_meal_keywords(meal_type_db)
        
        # 3. 프롬프트 합치기
        # (아까 내가 알려준 3D 렌더링 프롬프트랑 합쳐지면 더 좋음)
        final_prompt = self.base_prompt.format(
            meal_keywords=meal_keywords, 
            menu_items=f"Korean style {english_menu}"
        )
        return final_prompt