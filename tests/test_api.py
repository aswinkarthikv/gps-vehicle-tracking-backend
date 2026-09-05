import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.init_db import init_db

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

db = TestingSessionLocal()
init_db(db, bind_engine=test_engine)
db.close()

client = TestClient(app)

def test_login_user_a():
    response = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "usera"

def test_login_user_b():
    response = client.post("/api/auth/login", json={"username": "userb", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "userb"

def test_user_a_assigned_route_and_vehicle():
    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    route_resp = client.get("/api/user/assigned-route", headers=headers)
    assert route_resp.status_code == 200
    route_data = route_resp.json()
    assert route_data["route_code"] == "ROUTE-101"

    veh_resp = client.get("/api/user/assigned-vehicle", headers=headers)
    assert veh_resp.status_code == 200
    veh_data = veh_resp.json()
    assert veh_data["vehicle_number"] == "BUS-001"

def test_query_vehicle_location():
    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token_a = login_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    resp1 = client.get("/api/vehicles/1/current-location", headers=headers_a)
    assert resp1.status_code == 200
    assert resp1.json()["vehicle_number"] == "BUS-001"

    resp2 = client.get("/api/vehicles/2/current-location", headers=headers_a)
    assert resp2.status_code == 200
    assert resp2.json()["vehicle_number"] == "BUS-002"

def test_gps_telemetry_ingestion_and_tracking():
    new_gps = {
        "vehicle_id": 1,
        "latitude": 13.0750,
        "longitude": 80.2680,
        "speed": 45.2,
        "heading": 215.0
    }
    ingest_resp = client.post("/api/gps/ingest", json=new_gps)
    assert ingest_resp.status_code == 201

    login_resp = client.post("/api/auth/login", json={"username": "usera", "password": "password123"})
    token_a = login_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    track_resp = client.get("/api/tracking/current", headers=headers_a)
    assert track_resp.status_code == 200
    assert track_resp.json()["latitude"] == 13.0750
