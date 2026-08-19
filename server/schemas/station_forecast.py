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
   # 1년치(2025-07~2026-06) 범위가 -13.1~37.6로 크게 넓어짐
   # 물리적으로 말이 안 되는 값(예: -50, 200)은 API 단에서 먼저 걸러냄
   # 서울의 관측 역사상 극값(-32.6 ~ 39.6)보다 약간 여유를 둔 범위로 설정.
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
   # ===== 추가: 입력이 모델의 실제 학습 범위를 벗어나 신뢰도가 낮을 때 알려주는 플래그 =====
   # weather_service.get_weather_factor()가 클램핑(clamp)을 수행했다면 True로 채워짐.
   # 프론트에서 "이 예측은 학습 범위를 벗어난 날씨라 참고용입니다" 같은 안내에 사용 가능.
   weather_extrapolated: bool = Field(
      default=False,
      description="입력된 날씨 값이 날씨 모델의 학습 범위를 벗어나 근사(클램핑)되었는지 여부",
   )
   # ===== 추가 끝 =====
   message: str