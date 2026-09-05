from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class Waypoint(BaseModel):
    name: str
    latitude: float
    longitude: float
    is_stop: bool = False
    sequence: int

class BusRouteBase(BaseModel):
    route_code: str
    route_name: str
    start_point: str
    end_point: str
    waypoints_json: str

class BusRouteCreate(BusRouteBase):
    pass

class BusRouteResponse(BaseModel):
    id: int
    route_code: str
    route_name: str
    start_point: str
    end_point: str
    waypoints: List[Waypoint] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
