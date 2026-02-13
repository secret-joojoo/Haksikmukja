import httpx
from bs4 import BeautifulSoup
from datetime import date
from typing import List, Optional  # 타입 힌트 추가
from app.schemas.crawler import SchoolData, CafeteriaData, MenuData

class BaseScraper:
    def __init__(self, school_name, school_region, url):
        self.school_name = school_name
        self.school_region = school_region
        self.url = url

    async def fetch_html(self, *args, **kwargs):
        """사이트에 접속해서 HTML 원본을 가져오는 함수"""
        # 자식 클래스에서 인자를 다르게 받을 수 있으므로 유연하게 처리
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.get(self.url)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"❌ 접속 실패! 상태 코드: {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ 요청 중 에러 발생: {e}")
                return None

    async def parse(self, target_date: date) -> Optional[SchoolData]:
        """HTML을 분석해서 데이터를 뽑아내는 함수 (학교마다 오버라이딩 필수)"""
        # 기본 동작은 없으므로 None 반환 혹은 NotImplementedError 발생
        return None


def get_scrapers() -> List[BaseScraper]:
    from app.services.crawler.parsers.kaist import KaistScraper
    from app.services.crawler.parsers.kaisteast import KaisteastScraper
    from app.services.crawler.parsers.snu import SnuScraper
    # from app.services.crawler.parsers.sookmyung import SookmyungScraper
    from app.services.crawler.parsers.ewha import EwhaScraper
    from app.services.crawler.parsers.cnu import CnuScraper

    return [
        KaistScraper(),
        KaisteastScraper(),
        SnuScraper(),
        # SookmyungScraper(), 
        EwhaScraper(),      
        CnuScraper(),
    ]