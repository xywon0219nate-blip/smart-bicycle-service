from typing import Optional
from pydantic import BaseModel


class StationStatusItem(BaseModel):
   id: int
   name: str
   distance: Optional[str] = None  # 이제 위도/경도 기반 실제 거리("1.2km")가 채워짐
   available: int
   total: int
   status: str  # "GOOD" | "LOW" | "EMPTY"


class HourlyUsageItem(BaseModel):
   hour: str
   count: int


class StationStatusResponse(BaseModel):
   stations: list[StationStatusItem]
   hourlyUsage: list[HourlyUsageItem]