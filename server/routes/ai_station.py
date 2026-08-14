from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from schemas.station_forecast import StationInfo, StationForecastRequest, StationForecastResponse
from models.station_forecast_log import StationForecastLog
from database.connection import get_db

station_ai_router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
ML_DIR = BASE_DIR / "ML/models"
DATA_DIR = BASE_DIR / "ML/models"

# ===== 모델/데이터 로드 (서버 시작 시 한 번만) =====
_station_model = joblib.load(ML_DIR / "station_demand_model.pkl")
_district_encoder = joblib.load(ML_DIR / "district_encoder.pkl")
_weather_model = joblib.load(ML_DIR / "weather_effect_model_202606.pkl")
_weather_ref = pd.read_csv(DATA_DIR / "weather_reference_202606.csv")
_station_master = pd.read_csv(DATA_DIR / "station_master.csv")

# 🛠️ [수정된 부분] 데이터 전처리 과정 추가
# 1) 거치대 수(rack_count)에 빈칸(NaN)이 있으면 0으로 채워 float NaN -> int 변환 에러 방지
_station_master["rack_count"] = _station_master["rack_count"].fillna(0)
# 2) 만약 대여소 ID(station_id) 자체가 없는 껍데기 데이터가 섞여 있다면 해당 줄 삭제
_station_master = _station_master.dropna(subset=['station_id'])

# station_name 컬럼이 아직 없을 수 있으니 방어적으로 처리 (없으면 "대여소 {id}"로 표시)
if "station_name" not in _station_master.columns:
   _station_master["station_name"] = None
# =====================================================


def _station_display_name(row) -> str:
   name = row.station_name
   if isinstance(name, str) and name.strip():
      return name
   return f"대여소 {int(row.station_id)}"


def _encode_district(district: str) -> int:
   # 학습 때 없던 구(district)가 들어오면 "알수없음"으로 폴백 (LabelEncoder는 모르는 값이면 에러를 던짐)
   if district in _district_encoder.classes_:
      return int(_district_encoder.transform([district])[0])
   return int(_district_encoder.transform(["알수없음"])[0])


# 대여소 목록 조회 — 프론트의 대여소 선택 드롭다운용
@station_ai_router.get("/bike/seoul/stations", response_model=list[StationInfo])
async def list_stations(
   district: Optional[str] = Query(None, description="구 이름으로 필터 (예: 마포구)"),
   limit: int = Query(50, ge=1, le=500),
):
   # 1) 구(district)를 선택하지 않았다면, 빈 리스트를 보내어 화면에 아무것도 안 뜨게 만듭니다.
   if not district:
      return []

   # 2) 프론트에서 전달받은 구(district)와 정확히 일치하는 대여소만 골라냅니다.
   df = _station_master[_station_master["district"] == district]

   df = df.head(limit)
   return [
      StationInfo(
         station_id=int(row.station_id),
         name=_station_display_name(row),
         district=row.district,
         rack_count=int(row.rack_count),
      )
      for row in df.itertuples()
   ]




# 구(district) 목록 — 프론트에서 지역 필터 드롭다운 채울 때 사용
@station_ai_router.get("/bike/seoul/districts", response_model=list[str])
async def list_districts():
   return sorted(d for d in _station_master["district"].dropna().unique().tolist() if d != "알수없음")


# 대여소별 + 날씨 반영 수요예측
# station_demand_model(대여소 패턴) x weather_effect_model(날씨 배율)을 조합해서 계산
@station_ai_router.post("/ai/bike/station-forecast", response_model=StationForecastResponse)
async def forecast_station_demand(
   req: StationForecastRequest,
   db: Session = Depends(get_db),
) -> StationForecastResponse:
   matched = _station_master[_station_master.station_id == req.station_id]
   if matched.empty:
      raise HTTPException(status_code=404, detail="존재하지 않는 대여소입니다.")
   row = matched.iloc[0]

   date = pd.to_datetime(req.date)
   day_of_week = int(date.dayofweek)
   is_weekend = int(day_of_week >= 5)
   district_enc = _encode_district(row.district)

   # 1) 대여소 기본 패턴 예측 (날씨 정보 없음)
   station_input = pd.DataFrame([{
      "station_id": req.station_id,
      "hour": req.hour,
      "day_of_week": day_of_week,
      "is_weekend": is_weekend,
      "rack_count": row.rack_count,
      "district_enc": district_enc,
   }])
   station_base = float(
      _station_model.predict(station_input[_station_model.feature_names_in_])[0]
   )

   # 2) 오늘 날씨 조건일 때 서울시 전체 예측치
   weather_input = pd.DataFrame([{
      "hour": req.hour,
      "day_of_week": day_of_week,
      "is_weekend": is_weekend,
      "temperature": req.temperature,
      "rainfall": req.rainfall,
      "wind_speed": req.wind_speed,
      "humidity": req.humidity,
   }])
   weather_pred = float(
      _weather_model.predict(weather_input[_weather_model.feature_names_in_])[0]
   )

   # 3) 같은 시간대의 평소(날씨 무관) 서울시 평균과 비교해서 "날씨 배율" 계산
   baseline_row = _weather_ref[
      (_weather_ref.hour == req.hour) & (_weather_ref.is_weekend == is_weekend)
   ]
   baseline = float(baseline_row.total_rentals.values[0]) if not baseline_row.empty else weather_pred
   weather_factor = (weather_pred / baseline) if baseline > 0 else 1.0
   weather_factor = max(0.3, min(weather_factor, 2.0))  # 극단적인 배율로 왜곡되는 것 방지

   # 4) 대여소 기본 패턴에 날씨 배율을 곱해서 최종 예측
   predicted_demand = max(0, round(station_base * weather_factor))
   
   # 거치대 수가 0이거나 없는 경우 에러를 막기 위해 기본값 1 적용
   rack_count = int(row.rack_count) if row.rack_count > 0 else 1
   capacity_ratio = predicted_demand / rack_count if rack_count else 0.0

   if capacity_ratio >= 0.8:
      demand_level = "높음"
      message = "이 대여소는 해당 시간대 수요가 매우 높을 것으로 예상됩니다. 자전거 재배치를 권장합니다."
   elif capacity_ratio >= 0.5:
      demand_level = "보통"
      message = "이 대여소는 해당 시간대 수요가 보통 수준으로 예상됩니다."
   else:
      demand_level = "낮음"
      message = "이 대여소는 해당 시간대 수요가 낮을 것으로 예상됩니다."

   # ===== DB 로그 저장 =====
   log = StationForecastLog(
      station_id=req.station_id,
      date=req.date,
      hour=req.hour,
      predicted_demand=predicted_demand,
      demand_level=demand_level,
      weather_factor=weather_factor,
   )
   db.add(log)
   db.commit()
   # ========================

   return StationForecastResponse(
      station=StationInfo(
         station_id=int(row.station_id),
         name=_station_display_name(row),
         district=row.district,
         rack_count=rack_count,
      ),
      predicted_demand=predicted_demand,
      capacity_ratio=round(capacity_ratio, 3),
      demand_level=demand_level,
      weather_factor=round(weather_factor, 3),
      message=message,
   )