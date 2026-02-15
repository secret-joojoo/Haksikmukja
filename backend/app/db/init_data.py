from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import School, Cafeteria

async def initialize_school_data(session: AsyncSession):
    """
    서버 시작 시 학교와 식당 기초 데이터를 DB에 보장하는 함수
    """
    print("🌱 [시스템] 기초 데이터 점검 및 초기화 시작...")

    # 여기에 등록하고 싶은 학교/식당 리스트를 다 적어둬
    target_data = [
        {
            "name": "KAIST",
            "region": "대전",
            "cafeterias": ["카이마루", "서맛골", "교수회관", "문지캠퍼스", "화암 기숙사 식당"]
        },
        {
            "name": "서울시립대학교",
            "region": "서울",
            "cafeterias": ["학생회관 1층", "이룸라운지", "양식당", "자연과학관"]
        }
    ]

    for school_info in target_data:
        # 1. 학교 확인 및 생성
        result = await session.execute(select(School).where(School.name == school_info["name"]))
        school = result.scalars().first()

        if not school:
            print(f"  ➕ 학교 생성: {school_info['name']}")
            school = School(name=school_info["name"], region=school_info["region"])
            session.add(school)
            await session.commit()
            await session.refresh(school)
        
        # 2. 식당 확인 및 생성
        for caf_name in school_info["cafeterias"]:
            c_result = await session.execute(
                select(Cafeteria).where(
                    Cafeteria.school_id == school.id,
                    Cafeteria.name == caf_name
                )
            )
            cafeteria = c_result.scalars().first()

            if not cafeteria:
                print(f"    ➕ 식당 추가: {caf_name} ({school.name})")
                session.add(Cafeteria(school_id=school.id, name=caf_name))
            
    await session.commit()
    print("✅ [시스템] 기초 데이터 준비 완료!")