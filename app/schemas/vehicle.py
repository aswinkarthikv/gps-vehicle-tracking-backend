from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class VehicleBase(BaseModel):
    vehicle_number: str
    model: str
    status: str = "ACTIVE"
    assigned_route_id: Optional[int] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: int
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_speed: Optional[float] = 0.0
    current_heading: Optional[float] = 0.0
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
