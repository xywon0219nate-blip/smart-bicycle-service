from typing import Literal
from pydantic import BaseModel, Field


class BikeForecastRequest(BaseModel):
   hour: int = Field(..., ge=0, le=23, description="예측 시각 (0~23시)")
   temperature: float = Field(..., description="기온 (섭씨)")
   humidity: int = Field(..., ge=0, le=100, description="습도 (%)")
   wind_speed: float = Field(..., ge=0, description="풍속 (m/s)")
   visibility: int = Field(..., ge=0, description="가시거리 (10m 단위)")
   dew_point: float = Field(..., description="이슬점 온도 (섭씨)")
   solar_radiation: float = Field(..., ge=0, description="일사량 (MJ/m2)")
   rainfall: float = Field(..., ge=0, description="강수량 (mm)")
   snowfall: float = Field(..., ge=0, description="적설량 (cm)")
   season: Literal["Spring", "Summer", "Autumn", "Winter"]
   holiday: Literal["Holiday", "No Holiday"]
   functioning_day: Literal["Yes", "No"]


class BikeForecastResponse(BaseModel):
   predicted_demand: int = Field(..., description="서울시 전체 예상 대여 건수")
   demand_level: Literal["낮음", "보통", "높음"]
   message: str