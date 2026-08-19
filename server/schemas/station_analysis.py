from pydantic import BaseModel


class MonthlyUsageItem(BaseModel):
    month: str  # "2025-07" 형식 (연-월, 두 연도에 걸친 데이터라 월 숫자만으로는 구분 X -> 이 형식 사용)
    count: int


class TopStationItem(BaseModel):
    name: str
    count: int


class AgeDistributionItem(BaseModel):
    age: str
    percent: float


class InsightItem(BaseModel):
    title: str
    description: str


class StationAnalysisResponse(BaseModel):
    periodLabel: str  # 예: "2025.07 ~ 2026.06" (프론트에서 "N년 월별 이용 추이" 대신 실제 기간을 보여줄 때 사용)
    monthlyUsage: list[MonthlyUsageItem]
    topStations: list[TopStationItem]
    ageDistribution: list[AgeDistributionItem]
    insights: list[InsightItem]