from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.ai import BikeForecastRequest, BikeForecastResponse
from models.prediction_log import BikeForecastLog
from database.connection import get_db

ai_router = APIRouter()

# ml_models/bike_demand_model.pkl 경로를 프로젝트 루트 기준으로 고정.
# main.py를 어느 위치에서 실행하든 항상 같은 파일을 찾도록 __file__ 기준 상대경로 사용.
MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "bike_demand_model.pkl"
_model = joblib.load(MODEL_PATH)


def _classify_demand(predicted: float) -> tuple[str, str]:
   # train_model.py 학습에 쓰인 실제 대여량 분포(대략 0~3500대) 기준으로 임의 구간 설정.
   # 데이터가 더 쌓이면 이 임계값은 실제 분포(사분위수 등) 기준으로 다시 조정하는 게 좋음.
   if predicted >= 2000:
      return "높음", "서울시 전체 대여 수요가 매우 높은 시간대로 예측됩니다."
   elif predicted >= 800:
      return "보통", "서울시 전체 대여 수요가 보통 수준으로 예측됩니다."
   else:
      return "낮음", "서울시 전체 대여 수요가 낮은 시간대로 예측됩니다."


@ai_router.post("/ai/bike/forecast", response_model=BikeForecastResponse)
async def forecast_bike_demand(
   req: BikeForecastRequest,
   db: Session = Depends(get_db),
) -> BikeForecastResponse:
   input_df = pd.DataFrame([req.model_dump()])

   # train_model.py / ai-server main.py와 동일한 방식으로 원-핫 인코딩 후
   # 학습 당시 컬럼 순서(model.feature_names_in_)에 맞춰 정렬 (핵심: 순서 안 맞으면 예측이 틀어짐)
   input_df = pd.get_dummies(input_df)
   input_df = input_df.reindex(columns=_model.feature_names_in_, fill_value=0)

   prediction = float(_model.predict(input_df)[0])
   predicted_demand = round(prediction)
   demand_level, message = _classify_demand(prediction)

   # ===== 예측 결과를 DB에 로그로 저장 (선택 사항이지만 추천) =====
   log = BikeForecastLog(
      hour=req.hour,
      temperature=req.temperature,
      humidity=req.humidity,
      season=req.season,
      holiday=req.holiday,
      functioning_day=req.functioning_day,
      predicted_demand=predicted_demand,
      demand_level=demand_level,
   )
   db.add(log)
   db.commit()
   # ==================================================================

   return BikeForecastResponse(
      predicted_demand=predicted_demand,
      demand_level=demand_level,
      message=message,
   )