import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.member import member_router
from routes.dashboard import dashboard_router
from routes.ai_station import station_ai_router
from database.connection import engine, Base
import models.member  # noqa: F401  (테이블 등록을 위해 import 필요)
import models.station_forecast_log  # noqa: F401  (테이블 등록을 위해 import 필요)

# ===== 수정 시작: bike_demand_model.pkl이 아직 프로젝트에 없어서 서버 자체가 죽던 문제 수정 =====
# routes/ai.py는 import되는 순간 joblib.load(MODEL_PATH)를 실행하는데, 파일이 없으면
# 그 즉시 FileNotFoundError로 서버 전체가 못 뜸.
# 지금은 DemandForecast.jsx가 이 구모델(/api/ai/bike/forecast)을 더 이상 호출하지 않으므로
# 라우터 등록을 빼둠. 나중에 필요해지면 아래 두 줄의 주석만 풀면 됨(파일은 그대로 프로젝트에 남겨둘 것).
# from routes.ai import ai_router
# import models.prediction_log  # noqa: F401
# ===== 수정 끝 =====

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = os.getenv(
   "FRONT_ORIGINS",
   "http://localhost:5173, http://localhost:3000"
).split(",")

app.add_middleware(
   CORSMiddleware,
   allow_origins=[o.strip() for o in origins],
   allow_credentials=True,
   allow_methods=["GET", "POST", "PUT", "DELETE"],
   allow_headers=["*"],
)

app.include_router(member_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api")
# app.include_router(ai_router, prefix="/api")  # bike_demand_model.pkl 넣기 전까진 비활성화
app.include_router(station_ai_router, prefix="/api")


@app.get("/")
def root():
   return {"message": "PEDALUP backend alive"}