import urllib.parse
import random

class ImageGenerator:
    def __init__(self):
        # 무료 AI 서비스 (Pollinations.ai) 사용
        # 별도의 API Key가 필요 없음! 무제한 무료!
        self.base_url = "https://image.pollinations.ai/prompt/"

    async def generate_image(self, prompt: str) -> str:
        """
        프롬프트를 URL에 넣어서 이미지를 생성하는 링크를 반환함.
        내 컴퓨터의 GPU를 쓰지 않고, 외부 서버에서 연산함.
        """
        print(f"🎨 [AI 생성 요청] {prompt[:30]}...")
        
        # 1. 프롬프트를 URL 안전한 문자열로 변환 (공백 -> %20 등)
        encoded_prompt = urllib.parse.quote(prompt)
        
        # 2. 랜덤 시드 추가 (매번 다른 그림이 나오게 함)
        seed = random.randint(1, 999999)
        
        # 3. 최종 URL 완성 
        # width, height: 해상도 (1024 추천)
        # model=flux: 최신 Flux 모델 사용 (퀄리티 좋음)
        # nologo=true: 워터마크 제거
        # enhance=true: 프롬프트 자동 보정 (더 예쁘게 나옴)
        final_url = f"{self.base_url}{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true&enhance=true"
        
        print(f"✅ 생성된 URL: {final_url}")
        
        # 파일 경로가 아니라, 인터넷 주소(URL)를 바로 반환함
        return final_url