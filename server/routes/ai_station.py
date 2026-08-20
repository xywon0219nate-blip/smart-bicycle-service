from pathlib import Path
from typing import Optional

import joblib
import json
import math
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from schemas.station_forecast import StationInfo, StationForecastRequest, StationForecastResponse
from schemas.station_status import StationStatusResponse, StationStatusItem, HourlyUsageItem
from schemas.station_analysis import StationAnalysisResponse
from models.station_forecast_log import StationForecastLog
from database.connection import get_db

station_ai_router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
ML_DIR = BASE_DIR / "ML" / "models"
DATA_DIR = BASE_DIR / "ML" / "models"

import logging

logger = logging.getLogger(__name__)

_PERIOD_TAG = "202507_202606"

_station_model = None
_district_encoder = None
_weather_model = None
_weather_ref = None
_station_master = None
_MODELS_READY = False
_analysis_data = None
_ANALYSIS_READY = False


try:
   _station_model = joblib.load(ML_DIR / f"station_demand_model_{_PERIOD_TAG}.pkl")
   _district_encoder = joblib.load(ML_DIR / f"district_encoder_{_PERIOD_TAG}.pkl")
   _weather_model = joblib.load(ML_DIR / f"weather_effect_model_{_PERIOD_TAG}.pkl")
   _weather_ref = pd.read_csv(DATA_DIR / f"weather_reference_{_PERIOD_TAG}.csv")
   # station_master_{PERIOD_TAG}.csv: station_id, station_name, district, dong, latitude, longitude, rack_count
   _station_master = pd.read_csv(DATA_DIR / f"station_master_{_PERIOD_TAG}.csv")

   before = len(_station_master)
   _station_master = _station_master.dropna(subset=["rack_count", "district", "latitude", "longitude"]).copy()
   _station_master["rack_count"] = _station_master["rack_count"].astype(int)
   excluded = before - len(_station_master)
   if excluded > 0:
      logger.warning(
         "station_master_%s.csv에서 결측 %d건을 제외했습니다 (원본 %d건 -> %d건).",
         _PERIOD_TAG, excluded, before, len(_station_master),
      )
   if "dong" in _station_master.columns:
      _station_master["dong"] = _station_master["dong"].replace("알수없음", pd.NA)
   _MODELS_READY = True
except FileNotFoundError as e:
   logger.warning(
      "대여소 예측 모델/데이터 파일을 찾을 수 없어 관련 API가 비활성화됩니다: %s\n"
      "ML/models/ 폴더에 %s 기간 태그가 붙은 파일이 들어있는지 확인해주세요.",
      e, _PERIOD_TAG,
   )

try:
   with open(ML_DIR / f"analysis_summary_{_PERIOD_TAG}.json", encoding="utf-8") as f:
      _analysis_data = json.load(f)
   _ANALYSIS_READY = True
except FileNotFoundError as e:
   logger.warning(
      "AI 분석 페이지용 집계 파일을 찾을 수 없어 관련 API가 비활성화됩니다: %s\n",
      e, _PERIOD_TAG,
   )



def _require_models():
   if not _MODELS_READY:
      raise HTTPException(
         status_code=503,
         detail="대여소 예측 모델이 아직 로드되지 않았습니다. ML/models/ 폴더의 파일을 확인해주세요.",
      )


def _station_display_name(row) -> str:
   name = row.station_name
   if isinstance(name, str) and name.strip():
      return name
   return f"대여소 {int(row.station_id)}"


def _station_dong(row) -> Optional[str]:
   dong = getattr(row, "dong", None)
   if dong is None or (isinstance(dong, float) and pd.isna(dong)):
      return None
   dong = str(dong).strip()
   return dong if dong and dong != "알수없음" else None


def _encode_district(district: str) -> int:
   if district in _district_encoder.classes_:
      return int(_district_encoder.transform([district])[0])
   return int(_district_encoder.transform(["알수없음"])[0])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
   R = 6371.0
   phi1, phi2 = math.radians(lat1), math.radians(lat2)
   dphi = math.radians(lat2 - lat1)
   dlambda = math.radians(lon2 - lon1)
   a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
   return 2 * R * math.asin(math.sqrt(a))


def _pct_change(current: float, previous: float) -> Optional[float]:
   """previous가 0이면(비교 기준이 없으면) None을 돌려줌 -> 프론트에서 화살표를 안 보여줌."""
   if previous <= 0:
      return None
   return round((current - previous) / previous * 100, 1)


def _predict_station_demand(station_id: int, row, date, hour: int, temperature: float, humidity: int,
                             rainfall: float, wind_speed: float) -> tuple[float, float]:
   day_of_week = int(date.dayofweek)
   is_weekend = int(day_of_week >= 5)
   district_enc = _encode_district(row.district)

   station_input = pd.DataFrame([{
      "station_id": station_id, "hour": hour, "day_of_week": day_of_week,
      "is_weekend": is_weekend, "rack_count": row.rack_count, "district_enc": district_enc,
      "month": int(date.month),
   }])
   station_base = float(_station_model.predict(station_input[_station_model.feature_names_in_])[0])

   weather_input = pd.DataFrame([{
      "hour": hour, "day_of_week": day_of_week, "is_weekend": is_weekend,
      "temperature": temperature, "rainfall": rainfall, "wind_speed": wind_speed, "humidity": humidity,
   }])
   weather_pred = float(_weather_model.predict(weather_input[_weather_model.feature_names_in_])[0])

   baseline_row = _weather_ref[(_weather_ref.hour == hour) & (_weather_ref.is_weekend == is_weekend)]
   baseline = float(baseline_row.total_rentals.values[0]) if not baseline_row.empty else weather_pred
   weather_factor = max(0.3, min((weather_pred / baseline) if baseline > 0 else 1.0, 2.0))

   return station_base * weather_factor, weather_factor


def _station_hourly_curve(station_id: int, row, date) -> list[dict]:
   """해당 대여소의 '오늘' 요일 기준 0~23시 예상 이용량 커브 (날씨 보정 없이, 순수 대여소×시간 패턴)."""
   day_of_week = int(date.dayofweek)
   is_weekend = int(day_of_week >= 5)
   district_enc = _encode_district(row.district)

   rows = pd.DataFrame([{
      "station_id": station_id, "hour": h, "day_of_week": day_of_week,
      "is_weekend": is_weekend, "rack_count": row.rack_count, "district_enc": district_enc,
      "month": int(date.month),
   } for h in range(24)])
   preds = _station_model.predict(rows[_station_model.feature_names_in_])
   return [{"hour": f"{h}시", "count": max(0, round(p))} for h, p in enumerate(preds)]


@station_ai_router.get("/ai/bike/stations", response_model=list[StationInfo])
async def list_stations(
   district: Optional[str] = Query(None),
   limit: int = Query(50, ge=1, le=500),
):
   _require_models()
   df = _station_master
   if district:
      df = df[df["district"] == district]
   df = df.head(limit)
   return [
      StationInfo(
         station_id=int(row.station_id), name=_station_display_name(row),
         district=row.district, dong=_station_dong(row), rack_count=int(row.rack_count),
         latitude=float(row.latitude), longitude=float(row.longitude),
      )
      for row in df.itertuples()
   ]


@station_ai_router.get("/ai/bike/districts", response_model=list[str])
async def list_districts():
   _require_models()
   return sorted(d for d in _station_master["district"].dropna().unique().tolist() if d != "알수없음")


@station_ai_router.post("/ai/bike/station-forecast", response_model=StationForecastResponse)
async def forecast_station_demand(req: StationForecastRequest, db: Session = Depends(get_db)) -> StationForecastResponse:
   _require_models()
   matched = _station_master[_station_master.station_id == req.station_id]
   if matched.empty:
      raise HTTPException(status_code=404, detail="존재하지 않는 대여소입니다.")
   row = matched.iloc[0]
   date = pd.to_datetime(req.date)

   predicted_raw, weather_factor = _predict_station_demand(
      req.station_id, row, date, req.hour, req.temperature, req.humidity, req.rainfall, req.wind_speed,
   )
   predicted_demand = max(0, round(predicted_raw))
   rack_count = int(row.rack_count) if row.rack_count else 1
   capacity_ratio = predicted_demand / rack_count if rack_count else 0.0

   day_curve = _station_hourly_curve(req.station_id, row, date)
   pattern_sum = sum(item["count"] for item in day_curve)
   daily_total_demand = int(round(pattern_sum * weather_factor))

   prev_date = date - pd.Timedelta(days=1)
   prev_predicted_raw, _ = _predict_station_demand(
      req.station_id, row, prev_date, req.hour, req.temperature, req.humidity, req.rainfall, req.wind_speed,
   )
   prev_predicted_demand = max(0, round(prev_predicted_raw))
   hourly_demand_trend_pct = _pct_change(predicted_demand, prev_predicted_demand)

   prev_day_curve = _station_hourly_curve(req.station_id, row, prev_date)
   prev_pattern_sum = sum(item["count"] for item in prev_day_curve)
   daily_total_trend_pct = _pct_change(pattern_sum, prev_pattern_sum)


   if capacity_ratio >= 0.8:
      demand_level, message = "높음", "이 대여소는 해당 시간대 수요가 매우 높을 것으로 예상됩니다. 자전거 재배치를 권장합니다."
   elif capacity_ratio >= 0.5:
      demand_level, message = "보통", "이 대여소는 해당 시간대 수요가 보통 수준으로 예상됩니다."
   else:
      demand_level, message = "낮음", "이 대여소는 해당 시간대 수요가 낮을 것으로 예상됩니다."

   db.add(StationForecastLog(
      station_id=req.station_id, date=req.date, hour=req.hour,
      predicted_demand=predicted_demand, demand_level=demand_level, weather_factor=weather_factor,
   ))
   db.commit()

   return StationForecastResponse(
      station=StationInfo(station_id=int(row.station_id), name=_station_display_name(row),
                           district=row.district, dong=_station_dong(row), rack_count=rack_count,
                           latitude=float(row.latitude), longitude=float(row.longitude)),
      predicted_demand=predicted_demand, capacity_ratio=round(capacity_ratio, 3),
      demand_level=demand_level, weather_factor=round(weather_factor, 3), message=message,
      daily_total_demand=daily_total_demand,
      hourly_demand_trend_pct=hourly_demand_trend_pct,
      daily_total_trend_pct=daily_total_trend_pct,
   )


# ===== "대여소 현황" — 선택한 대여소 기준 실제 거리순 인근 대여소 + 그 대여소의 시간대별 이용량 =====
_DEFAULT_WEATHER = {"temperature": 20.0, "humidity": 55, "rainfall": 0.0, "wind_speed": 2.0}


@station_ai_router.get("/bike/seoul/stations", response_model=StationStatusResponse)
async def get_station_status(
   station_id: Optional[int] = Query(None, description="기준 대여소 (AI 수요예측에서 선택한 대여소)"),
   limit: int = Query(6, ge=1, le=50),
   date: Optional[str] = Query(None, description="기준 날짜 (YYYY-MM-DD). 없으면 오늘"),
   hour: Optional[int] = Query(None, ge=0, le=23, description="기준 시각. 없으면 현재 시각"),
   temperature: Optional[float] = Query(None),
   humidity: Optional[int] = Query(None, ge=0, le=100),
   rainfall: Optional[float] = Query(None, ge=0),
   wind_speed: Optional[float] = Query(None, ge=0),
):
   _require_models()

   now = pd.Timestamp.now()
   base_date = pd.to_datetime(date) if date else now
   base_hour = hour if hour is not None else now.hour
   weather = {
      "temperature": temperature if temperature is not None else _DEFAULT_WEATHER["temperature"],
      "humidity": humidity if humidity is not None else _DEFAULT_WEATHER["humidity"],
      "rainfall": rainfall if rainfall is not None else _DEFAULT_WEATHER["rainfall"],
      "wind_speed": wind_speed if wind_speed is not None else _DEFAULT_WEATHER["wind_speed"],
   }

   if station_id is not None:
      matched = _station_master[_station_master.station_id == station_id]
      if matched.empty:
         raise HTTPException(status_code=404, detail="존재하지 않는 대여소입니다.")
      center = matched.iloc[0]
   else:
      # 기준 대여소를 아직 안 골랐으면 첫 번째 대여소를 기본값으로 사용
      center = _station_master.iloc[0]

   # 실제 위도/경도 기반 거리 계산 -> 가까운 순 정렬 (자기 자신 포함)
   df = _station_master.copy()
   df["distance_km"] = df.apply(
      lambda r: _haversine_km(center.latitude, center.longitude, r.latitude, r.longitude), axis=1
   )
   nearby = df.sort_values("distance_km").head(limit)

   stations = []
   for row in nearby.itertuples():
      predicted_raw, _ = _predict_station_demand(
         int(row.station_id), row, base_date, base_hour,
         weather["temperature"], weather["humidity"],
         weather["rainfall"], weather["wind_speed"],
      )
      total = int(row.rack_count) if row.rack_count else 1
      available = max(0, min(total, round(total - predicted_raw)))

      if available == 0:
         status = "EMPTY"
      elif available / total < 0.25:
         status = "LOW"
      else:
         status = "GOOD"

      stations.append(StationStatusItem(
         id=int(row.station_id),
         name=_station_display_name(row),
         distance=f"{row.distance_km:.1f}km" if row.distance_km > 0 else "현재 위치",
         available=available,
         total=total,
         status=status,
      ))

   hourly_usage = [
      HourlyUsageItem(**item) for item in _station_hourly_curve(int(center.station_id), center, base_date)
   ]

   return StationStatusResponse(stations=stations, hourlyUsage=hourly_usage)


# ===== "AI 분석" 페이지 — 월별 이용 추이 / 인기 대여소 TOP 6 / 연령대별 이용 비율 =====

def _require_analysis():
   if not _ANALYSIS_READY:
      raise HTTPException(
         status_code=503,
         detail="분석 데이터가 아직 준비되지 않았습니다. analysis_summary 파일을 확인해주세요.",
      )


@station_ai_router.get("/ai/bike/analysis", response_model=StationAnalysisResponse)
async def get_analysis(
   year: Optional[int] = Query(None, description="조회할 연도 (예: 2026). year/month 둘 다 없으면 데이터상 가장 최근 달을 반환"),
   month: Optional[int] = Query(None, ge=1, le=12, description="조회할 월 (1~12)"),
):
   _require_analysis()

   monthly_usage = _analysis_data["monthlyUsage"]  # 노트북에서 시간순 정렬해 저장한 전체 기간 [{month, count}, ...]
   by_month = _analysis_data["byMonth"]

   if year is not None and month is not None:
      selected = f"{year:04d}-{month:02d}"
   else:
      selected = monthly_usage[-1]["month"]  # 기본값: 보유 데이터 중 가장 최근 달

   if selected not in by_month:
      raise HTTPException(
         status_code=404,
         detail=f"{selected} 데이터가 없습니다. 조회 가능한 기간을 확인해주세요.",
      )

   # 선택한 달까지의 "최근 12개월" 추이 (보유 데이터가 12개월 미만이면 있는 만큼만)
   idx = next(i for i, item in enumerate(monthly_usage) if item["month"] == selected)
   window = monthly_usage[max(0, idx - 11): idx + 1]

   month_detail = by_month[selected]


   current_month = window[-1]
   previous_month = window[-2] if len(window) >= 2 else None

   if previous_month and previous_month["count"] > 0:
      diff_pct = round((current_month["count"] - previous_month["count"]) / previous_month["count"] * 100, 1)
      is_up = diff_pct >= 0
      trend_insight = {
         "tag": "월별 트렌드",
         "icon": "TrendingUp" if is_up else "TrendingDown",
         "title": "전월 대비 이용량",
         "description": f"전월({previous_month['month']}) 대비 이용량이 {'증가' if is_up else '감소'}했습니다 ({diff_pct:+.1f}%).",
         "metricLabel": "전월 대비",
         "metricValue": f"{diff_pct:+.1f}%",
         "tone": "up" if is_up else "down",
      }
   else:
      # 데이터상 가장 첫 달이라 비교할 전월이 없는 경우
      trend_insight = {
         "tag": "월별 트렌드",
         "icon": "TrendingUp",
         "title": "이번 달 이용량",
         "description": f"{current_month['month']} 이용 건수는 {current_month['count']:,}건입니다 (비교 가능한 전월 데이터 없음).",
         "metricLabel": "이용건수",
         "metricValue": f"{current_month['count']:,}건",
         "tone": "neutral",
      }

   top_station = month_detail["topStations"][0]
   top_age = month_detail["ageDistribution"][0]

   insights = [
      trend_insight,
      {
         "tag": "대여소 순위",
         "icon": "MapPin",
         "title": "이 달 최고 인기 대여소",
         "description": f"'{top_station['name']}'이(가) {selected} 기준 가장 많이 이용됐습니다 ({top_station['count']:,}건).",
         "metricLabel": "이용건수",
         "metricValue": f"{top_station['count']:,}건",
         "tone": "neutral",
      },
      {
         "tag": "이용자 분석",
         "icon": "Users",
         "title": "이 달 주 이용 연령대",
         "description": f"'{top_age['age']}' 연령대가 {selected} 이용의 {top_age['percent']}%를 차지합니다.",
         "metricLabel": "비중",
         "metricValue": f"{top_age['percent']}%",
         "tone": "neutral",
      },
   ]

   return StationAnalysisResponse(
      periodLabel=f"{window[0]['month']} ~ {window[-1]['month']}",
      monthlyUsage=window,
      topStations=month_detail["topStations"],
      ageDistribution=month_detail["ageDistribution"],
      insights=insights,
   )