from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), unique=True, index=True, nullable=False)
    model = Column(String(100), nullable=False, default="Transit Bus")
    status = Column(String(50), nullable=False, default="ACTIVE")
    assigned_route_id = Column(Integer, ForeignKey("bus_routes.id"), nullable=True)

    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_speed = Column(Float, nullable=True, default=0.0)
    current_heading = Column(Float, nullable=True, default=0.0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)

    route = relationship("BusRoute", back_populates="vehicles")
    gps_logs = relationship("GPSData", back_populates="vehicle", cascade="all, delete-orphan")
    users = relationship("User", back_populates="assigned_vehicle")
