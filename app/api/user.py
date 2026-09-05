import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.route import BusRoute
from app.models.vehicle import Vehicle
from app.schemas.route import BusRouteResponse, Waypoint
from app.schemas.vehicle import VehicleResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/user", tags=["User & Assignments"])

@router.get("/assigned-route", response_model=BusRouteResponse)
def get_assigned_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the route assigned to the logged-in user.
    Enforces business logic: user can only see their assigned route.
    """
    if not current_user.assigned_route_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No route assigned to this user"
        )
    
    route = db.query(BusRoute).filter(BusRoute.id == current_user.assigned_route_id).first()
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned route not found"
        )
    
    raw_waypoints = json.loads(route.waypoints_json) if route.waypoints_json else []
    parsed_waypoints = [
        Waypoint(
            name=wp.get("name", ""),
            latitude=wp.get("latitude", 0.0),
            longitude=wp.get("longitude", 0.0),
            is_stop=wp.get("is_stop", False),
            sequence=wp.get("sequence", idx + 1)
        )
        for idx, wp in enumerate(raw_waypoints)
    ]

    return BusRouteResponse(
        id=route.id,
        route_code=route.route_code,
        route_name=route.route_name,
        start_point=route.start_point,
        end_point=route.end_point,
        waypoints=parsed_waypoints,
        created_at=route.created_at
    )

@router.get("/assigned-vehicle", response_model=VehicleResponse)
def get_assigned_vehicle(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the vehicle assigned to the logged-in user.
    Enforces business logic: user can only see their assigned vehicle.
    """
    if not current_user.assigned_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to this user"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.assigned_vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned vehicle not found"
        )
    
    return vehicle
