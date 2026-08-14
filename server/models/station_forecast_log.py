from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from database.connection import Base


class StationForecastLog(Base):
   __tablename__ = "station_forecast_log"

   id = Column(Integer, primary_key=True, index=True)
   station_id = Column(Integer, nullable=False, index=True)
   date = Column(String(10), nullable=False)
   hour = Column(Integer, nullable=False)
   predicted_demand = Column(Integer, nullable=False)
   demand_level = Column(String(10), nullable=False)
   weather_factor = Column(Float, nullable=False)
   created_at = Column(DateTime(timezone=True), server_default=func.now())