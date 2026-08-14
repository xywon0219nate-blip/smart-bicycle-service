import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.member import member_router
from routes.dashboard import dashboard_router
# from routes.ai import ai_router
from routes.ai_station import station_ai_router
from database.connection import engine, Base
import models.member  # noqa: F401  (테이블 등록을 위해 import 필요)
import models.prediction_log  # noqa: F401  (테이블 등록을 위해 import 필요)
import models.station_forecast_log  # noqa: F401  (테이블 등록을 위해 import 필요)

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = os.getenv(
   "FRONT_ORIGINS",
   "http://localhost:5173, http://localhost:3000"
).split(",")



app.add_middleware(
   CORSMiddleware,
   allow_origins=[
            "http://localhost:5173" ],# 프론트엔드 주소 허용
   allow_credentials=True,
   allow_methods=["GET", "POST", "PUT", "DELETE"],
   allow_headers=["*"],
)

app.include_router(member_router)
app.include_router(dashboard_router)
# app.include_router(ai_router, prefix="/api")
app.include_router(station_ai_router)


@app.get("/")
def root():
   return {"message": "PEDALUP backend alive"}