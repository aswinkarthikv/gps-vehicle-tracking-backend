# GPS Vehicle Tracking System - FastAPI Backend

A production-ready, modular **FastAPI** backend for a GPS-based vehicle tracking system. The service manages users, bus routes, vehicles, real-time GPS telemetry via **MQTT & REST API**, and enforces strict role-based route/vehicle authorization.

---

## 🌟 Key Features

- **Authentication & Security**: Secure JWT (JSON Web Token) authentication with `bcrypt` password hashing.
- **Strict Authorization**:
  - **User A** is assigned to **Route A** and **BUS-001** and can **only** access their assigned route and vehicle.
  - **User B** is assigned to **Route B** and **BUS-002** and can **only** access their assigned route and vehicle.
  - Access to unauthorized vehicle data is rejected with `403 Forbidden` at the backend layer.
- **Dual Telemetry Ingestion (MQTT & REST)**:
  - Background MQTT client subscribing to vehicle telemetry topics (`vehicle/telemetry/{vehicle_id}`).
  - REST endpoint (`POST /api/gps/ingest`) for direct telemetry ingestion.
- **GPS History & Real-Time Position**:
  - Maintains latest location on the vehicle entity for rapid dashboard lookup.
  - Stores indexed time-series logs for historical route trail plotting.
- **Built-in GPS Simulator**:
  - Standalone script simulating moving vehicles across realistic route waypoints with speed and heading calculation.
- **Containerization**: Full Docker & Docker Compose setup with PostgreSQL and Eclipse Mosquitto MQTT Broker.
- **Automated Test Suite**: Pytest test suite validating auth, route/vehicle isolation, security boundaries, and telemetry ingestion.

---

## 🏗️ Architecture & Tech Stack

```
[ GPS Simulator / IoT Device ]
               │
      (MQTT / REST Ingestion)
               ▼
[ FastAPI Backend (Python 3.12) ] ── (SQLAlchemy ORM) ──► [ PostgreSQL / SQLite ]
      ▲               │
 (JWT Auth)    (Strict Authorization Check)
      │               ▼
[ Flutter Mobile Application / Client ]
```

- **Framework**: FastAPI (Async Python 3.12)
- **Database**: PostgreSQL (Docker) / SQLite (Local standalone)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Auth**: Python-Jose (JWT), Passlib (Bcrypt)
- **MQTT**: Paho-MQTT v2

---

## 🗄️ Database Design (ER Model)

```
┌──────────────────────────┐         ┌──────────────────────────┐
│        bus_routes        │         │         vehicles         │
├──────────────────────────┤         ├──────────────────────────┤
│ id (PK)                  │1       *│ id (PK)                  │
│ route_code (UNIQUE)      ├─────────┤ vehicle_number (UNIQUE)  │
│ route_name               │         │ model                    │
│ start_point              │         │ status                   │
│ end_point                │         │ assigned_route_id (FK)   │
│ waypoints_json           │         │ current_latitude         │
│ created_at               │         │ current_longitude        │
└────────────┬─────────────┘         │ current_speed            │
             │1                      │ current_heading          │
             │                       │ last_updated             │
             │                       └────────────┬─────────────┘
             │                                    │1
             │                                    │
             │                                    │*
┌────────────▼─────────────┐         ┌────────────▼─────────────┐
│          users           │         │         gps_data         │
├──────────────────────────┤         ├──────────────────────────┤
│ id (PK)                  │         │ id (PK)                  │
│ username (UNIQUE)        │         │ vehicle_id (FK)          │
│ email (UNIQUE)           │         │ latitude                 │
│ hashed_password          │         │ longitude                │
│ full_name                │         │ speed                    │
│ role (USER / ADMIN)      │         │ heading                  │
│ assigned_route_id (FK)   │         │ timestamp                │
│ assigned_vehicle_id (FK) │         └──────────────────────────┘
└──────────────────────────┘
```

---

## 🚀 Quick Start & Local Run

### Prerequisites
- Python 3.11+ or Python 3.12
- Git

### 1. Setup Virtual Environment
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> The database will automatically initialize and seed with default demo users, routes, and vehicles on startup.

Interactive API Documentation (Swagger / OpenAPI):
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🐳 Running with Docker Compose

Run the entire stack (FastAPI Backend + PostgreSQL + Mosquitto MQTT Broker) with a single command:

```bash
docker compose up --build
```

Services exposed:
- **FastAPI Backend**: `http://localhost:8000`
- **Mosquitto MQTT Broker**: `localhost:1883`
- **PostgreSQL Database**: `localhost:5432`

---

## 👥 Seed Credentials for Testing

| Username | Password | Role | Assigned Route | Assigned Vehicle |
| :--- | :--- | :--- | :--- | :--- |
| `usera` | `password123` | USER | Route A (North Express - ROUTE-101) | BUS-001 (Volvo 9700 EV) |
| `userb` | `password123` | USER | Route B (South Coastal - ROUTE-202) | BUS-002 (Mercedes-Benz Citaro) |
| `admin` | `admin123` | ADMIN | All Routes (Full Access) | All Vehicles (Full Access) |

---

## 📡 GPS Telemetry Simulator

To simulate live moving vehicles along their respective bus routes:

```bash
# In a separate terminal with venv activated:
python -m app.services.gps_simulator both
```
- Transmits coordinates for **BUS-001** and **BUS-002** simultaneously via MQTT and REST API.
- Automatically calculates smooth interpolated GPS movements and heading bearings.

---

## 🧪 Running Automated Tests

Run the full pytest suite to verify authentication, authorization isolation, and telemetry ingestion:

```bash
pytest tests/test_api.py -v
```

---

## 📚 API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authenticate and retrieve JWT token | No |
| `GET` | `/api/auth/me` | Current user profile | Bearer Token |
| `GET` | `/api/user/assigned-route` | Retrieve logged-in user's assigned route & stops | Bearer Token |
| `GET` | `/api/user/assigned-vehicle` | Retrieve logged-in user's assigned vehicle | Bearer Token |
| `GET` | `/api/tracking/current` | Get live GPS position of assigned vehicle | Bearer Token |
| `GET` | `/api/tracking/history` | Get GPS historical breadcrumb path | Bearer Token |
| `GET` | `/api/vehicles/{id}/current-location` | Get vehicle location by ID (checks user assignment) | Bearer Token |
| `GET` | `/api/vehicles/{id}/history` | Get vehicle history by ID (checks user assignment) | Bearer Token |
| `POST` | `/api/gps/ingest` | Ingest vehicle GPS coordinate telemetry | No (Device/API Key) |
| `POST` | `/api/gps/simulate-step/{id}` | Advance vehicle to next waypoint | No |
