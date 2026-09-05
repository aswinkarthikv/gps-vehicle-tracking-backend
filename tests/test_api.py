import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.init_db import init_db

# Create test SQLite database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tracker.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Setup test DB
db = TestingSessionLocal()
init_db(db)
db.close()

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "GPS Vehicle Tracking System" in response.json()["message"]

def test_login_user_a():
    response = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "usera"
    assert data["role"] == "USER"

def test_login_user_b():
    response = client.post("/api/auth/login", json={"username": "userb", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "userb"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={"username": "usera", "password": "wrongpassword"})
    assert response.status_code == 401

def test_user_a_assigned_route_and_vehicle():
    # Login as User A
    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Assigned Route
    route_resp = client.get("/api/user/assigned-route", headers=headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()
    assert route_data["route_code"] == "ROUTE-101"
    assert "Route A" in route_data["route_name"]
    assert len(route_data["waypoints"]) > 0

    # Get Assigned Vehicle
    veh_resp = client.get("/api/user/assigned-vehicle", headers=headers)
    assert veh_resp.status_code == 200
    veh_data = veh_resp.json()
    assert veh_data["vehicle_number"] == "BUS-001"

def test_user_b_assigned_route_and_vehicle():
    # Login as User B
    login_resp = client.post("/api/auth/login", json={"username": "userb", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Assigned Route
    route_resp = client.get("/api/user/assigned-route", headers=headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()
    assert route_data["route_code"] == "ROUTE-202"
    assert "Route B" in route_data["route_name"]

    # Get Assigned Vehicle
    veh_resp = client.get("/api/user/assigned-vehicle", headers=headers)
    assert veh_resp.status_code == 200
    veh_data = veh_resp.json()
    assert veh_data["vehicle_number"] == "BUS-002"

def test_strict_authorization_enforcement():
    """
    CRITICAL REQUIREMENT:
    User A is assigned to BUS-001 (id=1).
    If User A attempts to access Vehicle 2 (BUS-002 assigned to User B),
    the backend MUST return 403 Forbidden.
    """
    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token_a = login_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A accesses own vehicle (id=1) -> Allowed
    own_resp = client.get("/api/vehicles/1/current-location", headers=headers_a)
    assert own_resp.status_code == 200
    assert own_resp.json()["vehicle_number"] == "BUS-001"

    # User A tries to access vehicle 2 -> FORBIDDEN (403)
    unauth_resp = client.get("/api/vehicles/2/current-location", headers=headers_a)
    assert unauth_resp.status_code == 403
    assert "Access Denied" in unauth_resp.json()["detail"]

    # User A tries to access vehicle 2 history -> FORBIDDEN (403)
    unauth_hist = client.get("/api/vehicles/2/history", headers=headers_a)
    assert unauth_hist.status_code == 403

def test_gps_telemetry_ingestion_and_tracking():
    # Ingest new GPS coordinate for Vehicle 1
    new_gps = {
        "vehicle_id": 1,
        "latitude": 13.0750,
        "longitude": 80.2680,
        "speed": 45.2,
        "heading": 215.0
    }
    ingest_resp = client.post("/api/gps/ingest", json=new_gps)
    assert ingest_resp.status_code == 201

    # Verify User A sees the updated current location
    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token_a = login_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    track_resp = client.get("/api/tracking/current", headers=headers_a)
    assert track_resp.status_code == 200
    track_data = track_resp.json()
    assert track_data["latitude"] == 13.0750
    assert track_data["longitude"] == 80.2680
    assert track_data["speed"] == 45.2

    # Verify history has entries
    hist_resp = client.get("/api/tracking/history", headers=headers_a)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["count"] > 0
