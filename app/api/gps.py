from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.vehicle import Vehicle
from app.models.gps_data import GPSData
from app.models.route import BusRoute
from app.schemas.gps_data import GPSDataCreate, GPSDataResponse

router = APIRouter(prefix="/gps", tags=["GPS Telemetry Ingestion"])

@router.post("/ingest", response_model=GPSDataResponse, status_code=status.HTTP_201_CREATED)
def ingest_gps_telemetry(payload: GPSDataCreate, db: Session = Depends(get_db)):
    """
    REST API endpoint for ingesting GPS telemetry data from vehicles/devices.
    Updates the latest vehicle position and appends to historical GPS logs.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {payload.vehicle_id} not found"
        )
    
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    
    # Update latest vehicle state
    vehicle.current_latitude = payload.latitude
    vehicle.current_longitude = payload.longitude
    vehicle.current_speed = payload.speed
    vehicle.current_heading = payload.heading
    vehicle.last_updated = timestamp
    vehicle.status = "IN_TRANSIT" if payload.speed > 2.0 else "IDLE"

    # Insert historical log
    gps_record = GPSData(
        vehicle_id=payload.vehicle_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        heading=payload.heading,
        timestamp=timestamp
    )
    db.add(gps_record)
    db.commit()
    db.refresh(gps_record)

    return gps_record

@router.post("/simulate-step/{vehicle_id}")
def simulate_vehicle_step(vehicle_id: int, db: Session = Depends(get_db)):
    """
    Simulate advancing a vehicle to the next waypoint on its assigned route.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle or not vehicle.route:
        raise HTTPException(status_code=404, detail="Vehicle or assigned route not found")
    
    waypoints = json.loads(vehicle.route.waypoints_json)
    if not waypoints:
        raise HTTPException(status_code=400, detail="No waypoints in route")

    # Find closest waypoint index or cycle forward
    current_idx = 0
    min_dist = float("inf")
    if vehicle.current_latitude and vehicle.current_longitude:
        for idx, wp in enumerate(waypoints):
            d = (wp["latitude"] - vehicle.current_latitude)**2 + (wp["longitude"] - vehicle.current_longitude)**2
            if d < min_dist:
                min_dist = d
                current_idx = idx
    
    next_idx = (current_idx + 1) % len(waypoints)
    target_wp = waypoints[next_idx]
    
    timestamp = datetime.now(timezone.utc)
    vehicle.current_latitude = target_wp["latitude"]
    vehicle.current_longitude = target_wp["longitude"]
    vehicle.current_speed = 35.0 if not target_wp.get("is_stop") else 0.0
    vehicle.last_updated = timestamp
    vehicle.status = "IN_TRANSIT" if vehicle.current_speed > 0 else "STOPPED"

    gps_record = GPSData(
        vehicle_id=vehicle.id,
        latitude=target_wp["latitude"],
        longitude=target_wp["longitude"],
        speed=vehicle.current_speed,
        heading=180.0,
        timestamp=timestamp
    )
    db.add(gps_record)
    db.commit()

    return {
        "message": f"Advanced {vehicle.vehicle_number} to waypoint {target_wp['name']}",
        "vehicle_id": vehicle.id,
        "location": {"latitude": target_wp["latitude"], "longitude": target_wp["longitude"]},
        "waypoint_name": target_wp["name"],
        "is_stop": target_wp.get("is_stop", False)
    }
