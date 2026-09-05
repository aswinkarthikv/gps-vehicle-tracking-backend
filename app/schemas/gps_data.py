from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class GPSDataCreate(BaseModel):
    vehicle_id: int
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(0.0, ge=0.0)
    heading: float = Field(0.0, ge=0.0, le=360.0)
    timestamp: Optional[datetime] = None

class GPSDataResponse(BaseModel):
    id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float
    heading: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class VehicleCurrentLocation(BaseModel):
    vehicle_id: int
    vehicle_number: str
    model: str
    status: str
    route_id: Optional[int] = None
    route_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    speed: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    last_updated: Optional[datetime] = None

class HistoricalGPSResponse(BaseModel):
    vehicle_id: int
    vehicle_number: str
    count: int
    history: List[GPSDataResponse]
