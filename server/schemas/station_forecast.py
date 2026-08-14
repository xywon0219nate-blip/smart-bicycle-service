from pydantic import BaseModel, Field


class StationInfo(BaseModel):
   station_id: int
   name: str
   district: str
   rack_count: int


# date는 "YYYY-MM-DD" 문자열로 받아서 서버에서 day_of_week/is_weekend를 파생시킴
# (bike_demand_model 연동 때와 동일한 이유: 파생 로직을 한 곳에만 두기 위함)
class StationForecastRequest(BaseModel):
   station_id: int
   date: str
   hour: int = Field(..., ge=0, le=23)
   temperature: float
   humidity: int = Field(..., ge=0, le=100)
   rainfall: float = Field(..., ge=0)
   wind_speed: float = Field(..., ge=0)


class StationForecastResponse(BaseModel):
   station: StationInfo
   predicted_demand: int = Field(..., description="이 대여소의 해당 시간대 예상 대여 건수")
   capacity_ratio: float = Field(..., description="예상 대여량 / 대여소 정원")
   demand_level: str
   weather_factor: float = Field(..., description="평소 대비 오늘 날씨로 인한 수요 배율")
   message: str