from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func

from database.connection import Base


# 수요예측 모델이 호출될 때마다 입력값 + 예측 결과를 한 줄씩 저장.
# 나중에 "최근 예측 이력", "월별 추이" 같은 화면을 이 테이블 조회로 만들 수 있음.
class BikeForecastLog(Base):
   __tablename__ = "bike_forecast_log"

   id = Column(Integer, primary_key=True, index=True)

   # 입력값
   hour = Column(Integer, nullable=False)
   temperature = Column(Float, nullable=False)
   humidity = Column(Integer, nullable=False)
   season = Column(String(10), nullable=False)
   holiday = Column(String(20), nullable=False)
   functioning_day = Column(String(5), nullable=False)

   # 예측 결과
   predicted_demand = Column(Integer, nullable=False)
   demand_level = Column(String(10), nullable=False)

   created_at = Column(DateTime(timezone=True), server_default=func.now())