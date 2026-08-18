from pathlib import Path
from typing import Optional

import joblib
import math
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from schemas.station_forecast import StationInfo, StationForecastRequest, StationForecastResponse
from schemas.station_status import StationStatusResponse, StationStatusItem, HourlyUsageItem
from models.station_forecast_log import StationForecastLog
from database.connection import get_db

station_ai_router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
ML_DIR = BASE_DIR / "ML" / "models"
DATA_DIR = BASE_DIR / "ML" / "models"

import logging

logger = logging.getLogger(__name__)

_station_model = None
_district_encoder = None
_weather_model = None
_weather_ref = None
_station_master = None
_MODELS_READY = False

try:
   _station_model = joblib.load(ML_DIR / "station_demand_model.pkl")
   _district_encoder = joblib.load(ML_DIR / "district_encoder.pkl")
   _weather_model = joblib.load(ML_DIR / "weather_effect_model_202606.pkl")
   _weather_ref = pd.read_csv(DATA_DIR / "weather_reference_202606.csv")
   # station_master_v2.csv: station_id, station_name, district, latitude, longitude, rack_count
   _station_master = pd.read_csv(DATA_DIR / "station_master_v2.csv")

   before = len(_station_master)
   _station_master = _station_master.dropna(subset=["rack_count", "district", "latitude", "longitude"]).copy()
   _station_master["rack_count"] = _station_master["rack_count"].astype(int)
   excluded = before - len(_station_master)
   if excluded > 0:
      logger.warning(
         "station_master_v2.csv에서 결측 %d건을 제외했습니다 (원본 %d건 -> %d건).",
         excluded, before, len(_station_master),
      )
   _MODELS_READY = True
except FileNotFoundError as e:
   logger.warning(
      "대여소 예측 모델/데이터 파일을 찾을 수 없어 관련 API가 비활성화됩니다: %s\n"
      "ML/models/ 폴더에 필요한 파일이 들어있는지 확인해주세요.",
      e,
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


def _predict_station_demand(station_id: int, row, date, hour: int, temperature: float, humidity: int,
                             rainfall: float, wind_speed: float) -> tuple[float, float]:
   day_of_week = int(date.dayofweek)
   is_weekend = int(day_of_week >= 5)
   district_enc = _encode_district(row.district)

   station_input = pd.DataFrame([{
      "station_id": station_id, "hour": hour, "day_of_week": day_of_week,
      "is_weekend": is_weekend, "rack_count": row.rack_count, "district_enc": district_enc,
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
         district=row.district, rack_count=int(row.rack_count),
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
                           district=row.district, rack_count=rack_count,
                           latitude=float(row.latitude), longitude=float(row.longitude)),
      predicted_demand=predicted_demand, capacity_ratio=round(capacity_ratio, 3),
      demand_level=demand_level, weather_factor=round(weather_factor, 3), message=message,
   )


# ===== "대여소 현황" — 선택한 대여소 기준 실제 거리순 인근 대여소 + 그 대여소의 시간대별 이용량 =====
_DEFAULT_WEATHER = {"temperature": 20.0, "humidity": 55, "rainfall": 0.0, "wind_speed": 2.0}


@station_ai_router.get("/bike/seoul/stations", response_model=StationStatusResponse)
async def get_station_status(
   station_id: Optional[int] = Query(None, description="기준 대여소 (AI 수요예측에서 선택한 대여소)"),
   limit: int = Query(6, ge=1, le=50),
):
   _require_models()

   now = pd.Timestamp.now()
   hour = now.hour

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
         int(row.station_id), row, now, hour,
         _DEFAULT_WEATHER["temperature"], _DEFAULT_WEATHER["humidity"],
         _DEFAULT_WEATHER["rainfall"], _DEFAULT_WEATHER["wind_speed"],
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
      HourlyUsageItem(**item) for item in _station_hourly_curve(int(center.station_id), center, now)
   ]

   return StationStatusResponse(stations=stations, hourlyUsage=hourly_usage)