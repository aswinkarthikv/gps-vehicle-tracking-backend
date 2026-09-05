from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.gps_data import GPSData
from app.schemas.gps_data import VehicleCurrentLocation, GPSDataResponse, HistoricalGPSResponse
from app.api.deps import get_current_user, enforce_vehicle_access

router = APIRouter(tags=["Tracking & GPS Telemetry"])

@router.get("/tracking/current", response_model=VehicleCurrentLocation)
def get_current_tracking_for_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current location of the assigned vehicle for the currently authenticated user.
    """
    if not current_user.assigned_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to current user"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.assigned_vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned vehicle not found"
        )
    
    route_name = vehicle.route.route_name if vehicle.route else None

    return VehicleCurrentLocation(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        model=vehicle.model,
        status=vehicle.status,
        route_id=vehicle.assigned_route_id,
        route_name=route_name,
        latitude=vehicle.current_latitude,
        longitude=vehicle.current_longitude,
        speed=vehicle.current_speed,
        heading=vehicle.current_heading,
        last_updated=vehicle.last_updated
    )

@router.get("/tracking/history", response_model=HistoricalGPSResponse)
def get_historical_tracking_for_user(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical GPS tracking points of the assigned vehicle for the currently authenticated user.
    """
    if not current_user.assigned_vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to current user"
        )
    
    vehicle = db.query(Vehicle).filter(Vehicle.id == current_user.assigned_vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned vehicle not found"
        )
    
    logs = (
        db.query(GPSData)
        .filter(GPSData.vehicle_id == vehicle.id)
        .order_by(GPSData.timestamp.asc())
        .limit(limit)
        .all()
    )

    return HistoricalGPSResponse(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        count=len(logs),
        history=[
            GPSDataResponse(
                id=log.id,
                vehicle_id=log.vehicle_id,
                latitude=log.latitude,
                longitude=log.longitude,
                speed=log.speed,
                heading=log.heading,
                timestamp=log.timestamp
            )
            for log in logs
        ]
    )

@router.get("/vehicles/{vehicle_id}/current-location", response_model=VehicleCurrentLocation)
def get_vehicle_current_location_by_id(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current location of a specific vehicle ID.
    Enforces strict authorization: User A can only access Vehicle A.
    """
    vehicle = enforce_vehicle_access(vehicle_id, current_user, db)
    route_name = vehicle.route.route_name if vehicle.route else None

    return VehicleCurrentLocation(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        model=vehicle.model,
        status=vehicle.status,
        route_id=vehicle.assigned_route_id,
        route_name=route_name,
        latitude=vehicle.current_latitude,
        longitude=vehicle.current_longitude,
        speed=vehicle.current_speed,
        heading=vehicle.current_heading,
        last_updated=vehicle.last_updated
    )

@router.get("/vehicles/{vehicle_id}/history", response_model=HistoricalGPSResponse)
def get_vehicle_history_by_id(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical GPS records for a specific vehicle ID.
    Enforces strict authorization: User A can only access Vehicle A.
    """
    vehicle = enforce_vehicle_access(vehicle_id, current_user, db)
    logs = (
        db.query(GPSData)
        .filter(GPSData.vehicle_id == vehicle.id)
        .order_by(GPSData.timestamp.asc())
        .limit(limit)
        .all()
    )

    return HistoricalGPSResponse(
        vehicle_id=vehicle.id,
        vehicle_number=vehicle.vehicle_number,
        count=len(logs),
        history=[
            GPSDataResponse(
                id=log.id,
                vehicle_id=log.vehicle_id,
                latitude=log.latitude,
                longitude=log.longitude,
                speed=log.speed,
                heading=log.heading,
                timestamp=log.timestamp
            )
            for log in logs
        ]
    )
