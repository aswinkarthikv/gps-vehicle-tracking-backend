import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine as default_engine, SessionLocal
from app.models.user import User
from app.models.route import BusRoute
from app.models.vehicle import Vehicle
from app.models.gps_data import GPSData
from app.core.security import get_password_hash

# Realistic GPS Waypoints for Route A
ROUTE_A_WAYPOINTS = [
    {"name": "Central Railway Station", "latitude": 13.0827, "longitude": 80.2707, "is_stop": True, "sequence": 1},
    {"name": "Government Estate", "latitude": 13.0694, "longitude": 80.2741, "is_stop": True, "sequence": 2},
    {"name": "LIC / Mount Road", "latitude": 13.0612, "longitude": 80.2642, "is_stop": False, "sequence": 3},
    {"name": "Thousand Lights", "latitude": 13.0560, "longitude": 80.2520, "is_stop": True, "sequence": 4},
    {"name": "Gemini Flyover", "latitude": 13.0489, "longitude": 80.2505, "is_stop": False, "sequence": 5},
    {"name": "T. Nagar Bus Terminus", "latitude": 13.0418, "longitude": 80.2341, "is_stop": True, "sequence": 6},
    {"name": "Saidapet Metro", "latitude": 13.0232, "longitude": 80.2223, "is_stop": True, "sequence": 7},
    {"name": "Guindy Industrial Estate", "latitude": 13.0067, "longitude": 80.2052, "is_stop": True, "sequence": 8},
    {"name": "Airport International Terminal", "latitude": 12.9856, "longitude": 80.1693, "is_stop": True, "sequence": 9},
    {"name": "Tech Park Campus OMR", "latitude": 12.9715, "longitude": 80.1601, "is_stop": True, "sequence": 10},
]

# Realistic GPS Waypoints for Route B
ROUTE_B_WAYPOINTS = [
    {"name": "Marina Beach Plaza", "latitude": 13.0500, "longitude": 80.2824, "is_stop": True, "sequence": 1},
    {"name": "Santhome Cathedral", "latitude": 13.0336, "longitude": 80.2778, "is_stop": True, "sequence": 2},
    {"name": "Adyar Signal", "latitude": 13.0064, "longitude": 80.2573, "is_stop": True, "sequence": 3},
    {"name": "IIT Madras Main Gate", "latitude": 13.0033, "longitude": 80.2392, "is_stop": True, "sequence": 4},
    {"name": "Tidel Park / Tharamani", "latitude": 12.9888, "longitude": 80.2476, "is_stop": True, "sequence": 5},
    {"name": "SRP Tools Junction", "latitude": 12.9774, "longitude": 80.2458, "is_stop": False, "sequence": 6},
    {"name": "Kandanchavadi OMR", "latitude": 12.9665, "longitude": 80.2443, "is_stop": True, "sequence": 7},
    {"name": "Perungudi Tech Hub", "latitude": 12.9560, "longitude": 80.2431, "is_stop": True, "sequence": 8},
    {"name": "Thoraipakkam Junction", "latitude": 12.9405, "longitude": 80.2370, "is_stop": True, "sequence": 9},
    {"name": "Innovation Valley Campus", "latitude": 12.9250, "longitude": 80.2300, "is_stop": True, "sequence": 10},
]

def init_db(db: Session, bind_engine=None) -> None:
    target_engine = bind_engine or db.get_bind() or default_engine
    Base.metadata.create_all(bind=target_engine)

    # 1. Seed Routes
    route_a = db.query(BusRoute).filter(BusRoute.route_code == "ROUTE-101").first()
    if not route_a:
        route_a = BusRoute(
            route_code="ROUTE-101",
            route_name="Route A (North Express)",
            start_point="Central Railway Station",
            end_point="Tech Park Campus OMR",
            waypoints_json=json.dumps(ROUTE_A_WAYPOINTS)
        )
        db.add(route_a)
        db.flush()

    route_b = db.query(BusRoute).filter(BusRoute.route_code == "ROUTE-202").first()
    if not route_b:
        route_b = BusRoute(
            route_code="ROUTE-202",
            route_name="Route B (South Coastal Link)",
            start_point="Marina Beach Plaza",
            end_point="Innovation Valley Campus",
            waypoints_json=json.dumps(ROUTE_B_WAYPOINTS)
        )
        db.add(route_b)
        db.flush()

    # 2. Seed Vehicles
    veh_a = db.query(Vehicle).filter(Vehicle.vehicle_number == "BUS-001").first()
    if not veh_a:
        veh_a = Vehicle(
            vehicle_number="BUS-001",
            model="Volvo 9700 EV",
            status="IN_TRANSIT",
            assigned_route_id=route_a.id,
            current_latitude=ROUTE_A_WAYPOINTS[0]["latitude"],
            current_longitude=ROUTE_A_WAYPOINTS[0]["longitude"],
            current_speed=38.5,
            current_heading=210.0,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(veh_a)
        db.flush()

    veh_b = db.query(Vehicle).filter(Vehicle.vehicle_number == "BUS-002").first()
    if not veh_b:
        veh_b = Vehicle(
            vehicle_number="BUS-002",
            model="Mercedes-Benz Citaro Hybrid",
            status="IN_TRANSIT",
            assigned_route_id=route_b.id,
            current_latitude=ROUTE_B_WAYPOINTS[0]["latitude"],
            current_longitude=ROUTE_B_WAYPOINTS[0]["longitude"],
            current_speed=42.0,
            current_heading=180.0,
            last_updated=datetime.now(timezone.utc)
        )
        db.add(veh_b)
        db.flush()

    # 3. Seed Initial GPS Trails
    now = datetime.now(timezone.utc)
    for i, pt in enumerate(ROUTE_A_WAYPOINTS[:4]):
        ts = now - timedelta(minutes=(4 - i) * 5)
        gps_log = GPSData(
            vehicle_id=veh_a.id,
            latitude=pt["latitude"],
            longitude=pt["longitude"],
            speed=35.0 + (i * 2),
            heading=200.0 + (i * 5),
            timestamp=ts
        )
        db.add(gps_log)

    for i, pt in enumerate(ROUTE_B_WAYPOINTS[:4]):
        ts = now - timedelta(minutes=(4 - i) * 5)
        gps_log = GPSData(
            vehicle_id=veh_b.id,
            latitude=pt["latitude"],
            longitude=pt["longitude"],
            speed=40.0 + (i * 1.5),
            heading=180.0 + (i * 4),
            timestamp=ts
        )
        db.add(gps_log)

    # 4. Seed Users with Strict Route & Vehicle Assignments
    user_a = db.query(User).filter(User.username == "usera").first()
    if not user_a:
        user_a = User(
            username="usera",
            email="usera@company.com",
            full_name="User A (North Commuter)",
            hashed_password=get_password_hash("password123"),
            role="USER",
            assigned_route_id=route_a.id,
            assigned_vehicle_id=veh_a.id
        )
        db.add(user_a)

    user_b = db.query(User).filter(User.username == "userb").first()
    if not user_b:
        user_b = User(
            username="userb",
            email="userb@company.com",
            full_name="User B (South Commuter)",
            hashed_password=get_password_hash("password123"),
            role="USER",
            assigned_route_id=route_b.id,
            assigned_vehicle_id=veh_b.id
        )
        db.add(user_b)

    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@company.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role="ADMIN",
            assigned_route_id=None,
            assigned_vehicle_id=None
        )
        db.add(admin_user)

    db.commit()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized successfully.")
    finally:
        db.close()
