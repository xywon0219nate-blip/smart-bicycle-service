import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.member import member_router
from database.connection import engine, Base
import models.member  # noqa: F401  (테이블 등록을 위해 import 필요)

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


@app.get("/")
def root():
   return {"message": "PEDALUP backend alive"}