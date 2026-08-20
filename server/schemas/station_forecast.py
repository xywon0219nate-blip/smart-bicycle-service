from typing import Optional

from pydantic import BaseModel, Field


class StationInfo(BaseModel):
   station_id: int
   name: str
   district: str
   dong: Optional[str] = None
   rack_count: int
   latitude: float
   longitude: float


class StationForecastRequest(BaseModel):
   station_id: int
   date: str
   hour: int = Field(..., ge=0, le=23)
   temperature: float = Field(..., ge=-40, le=50)
   humidity: int = Field(..., ge=0, le=100)
   rainfall: float = Field(..., ge=0)
   wind_speed: float = Field(..., ge=0)


class StationForecastResponse(BaseModel):
   station: StationInfo
   predicted_demand: int = Field(..., description="이 대여소의 해당 시간대 예상 대여 건수")
   capacity_ratio: float = Field(..., description="예상 대여량 / 대여소 정원")
   demand_level: str
   weather_factor: float = Field(..., description="평소 대비 오늘 날씨로 인한 수요 배율")
   weather_extrapolated: bool = Field(
      default=False,
      description="입력된 날씨 값이 날씨 모델의 학습 범위를 벗어나 근사(클램핑)되었는지 여부",
   )
   daily_total_demand: int = Field(..., description="선택한 날짜(0~23시) 기준 예상 총 대여 건수")
   hourly_demand_trend_pct: Optional[float] = Field(
      None, description="이 시간대 예상 대여량의 전일 동시간대 대비 증감률(%)"
   )
   daily_total_trend_pct: Optional[float] = Field(
      None, description="선택 날짜 총 예상 대여량의 전일 대비 증감률(%)"
   )

   message: str