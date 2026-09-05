import time
import json
import math
import random
from datetime import datetime, timezone
import requests
import paho.mqtt.client as mqtt
from app.core.config import settings

API_URL = "http://localhost:8000/api/gps/ingest"

ROUTE_A_WAYPOINTS = [
    {"name": "Central Railway Station", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Government Estate", "latitude": 13.0694, "longitude": 80.2741},
    {"name": "LIC / Mount Road", "latitude": 13.0612, "longitude": 80.2642},
    {"name": "Thousand Lights", "latitude": 13.0560, "longitude": 80.2520},
    {"name": "Gemini Flyover", "latitude": 13.0489, "longitude": 80.2505},
    {"name": "T. Nagar Bus Terminus", "latitude": 13.0418, "longitude": 80.2341},
    {"name": "Saidapet Metro", "latitude": 13.0232, "longitude": 80.2223},
    {"name": "Guindy Industrial Estate", "latitude": 13.0067, "longitude": 80.2052},
    {"name": "Airport International Terminal", "latitude": 12.9856, "longitude": 80.1693},
    {"name": "Tech Park Campus OMR", "latitude": 12.9715, "longitude": 80.1601},
]

ROUTE_B_WAYPOINTS = [
    {"name": "Marina Beach Plaza", "latitude": 13.0500, "longitude": 80.2824},
    {"name": "Santhome Cathedral", "latitude": 13.0336, "longitude": 80.2778},
    {"name": "Adyar Signal", "latitude": 13.0064, "longitude": 80.2573},
    {"name": "IIT Madras Main Gate", "latitude": 13.0033, "longitude": 80.2392},
    {"name": "Tidel Park / Tharamani", "latitude": 12.9888, "longitude": 80.2476},
    {"name": "SRP Tools Junction", "latitude": 12.9774, "longitude": 80.2458},
    {"name": "Kandanchavadi OMR", "latitude": 12.9665, "longitude": 80.2443},
    {"name": "Perungudi Tech Hub", "latitude": 12.9560, "longitude": 80.2431},
    {"name": "Thoraipakkam Junction", "latitude": 12.9405, "longitude": 80.2370},
    {"name": "Innovation Valley Campus", "latitude": 12.9250, "longitude": 80.2300},
]

def interpolate_points(p1, p2, steps=15):
    """Interpolate finely between two waypoints for realistic smooth driving."""
    points = []
    for step in range(steps):
        t = step / float(steps)
        lat = p1["latitude"] + t * (p2["latitude"] - p1["latitude"])
        lng = p1["longitude"] + t * (p2["longitude"] - p1["longitude"])
        points.append((lat, lng))
    return points

def calculate_heading(lat1, lon1, lat2, lon2):
    """Calculate bearing heading in degrees."""
    dLon = math.radians(lon2 - lon1)
    y = math.sin(dLon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def build_ping_pong_path(waypoints, steps_per_leg=12):
    """
    Build a continuous forward and return journey (Origin -> Destination -> Origin)
    so the bus moves continuously along the roads without ever jumping or teleporting.
    """
    points = []
    # 1. Forward Journey (0 to N-1)
    for i in range(len(waypoints) - 1):
        points.extend(interpolate_points(waypoints[i], waypoints[i + 1], steps=steps_per_leg))
    
    # 2. Return Journey (N-1 back to 0)
    for i in range(len(waypoints) - 1, 0, -1):
        points.extend(interpolate_points(waypoints[i], waypoints[i - 1], steps=steps_per_leg))
        
    return points

def run_simulator(mode="rest", interval_seconds=2):
    """
    Simulates smooth, realistic GPS telemetry step-by-step along the scheduled bus route.
    """
    print(f"=== Starting Smooth GPS Transit Simulator (Ping-Pong Continuous Path) ===")
    path_a = build_ping_pong_path(ROUTE_A_WAYPOINTS, steps_per_leg=14)
    path_b = build_ping_pong_path(ROUTE_B_WAYPOINTS, steps_per_leg=14)

    step_a = 0
    step_b = len(path_b) // 3

    while True:
        try:
            # 1. Vehicle 1 (BUS-001)
            curr_a = path_a[step_a]
            next_a = path_a[(step_a + 1) % len(path_a)]
            heading_a = calculate_heading(curr_a[0], curr_a[1], next_a[0], next_a[1])
            speed_a = round(random.uniform(34.0, 46.0), 1)

            payload_a = {
                "vehicle_id": 1,
                "latitude": round(curr_a[0], 6),
                "longitude": round(curr_a[1], 6),
                "speed": speed_a,
                "heading": round(heading_a, 1),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # 2. Vehicle 2 (BUS-002)
            curr_b = path_b[step_b]
            next_b = path_b[(step_b + 1) % len(path_b)]
            heading_b = calculate_heading(curr_b[0], curr_b[1], next_b[0], next_b[1])
            speed_b = round(random.uniform(30.0, 42.0), 1)

            payload_b = {
                "vehicle_id": 2,
                "latitude": round(curr_b[0], 6),
                "longitude": round(curr_b[1], 6),
                "speed": speed_b,
                "heading": round(heading_b, 1),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Ingest via REST API
            requests.post(API_URL, json=payload_a, timeout=1.5)
            requests.post(API_URL, json=payload_b, timeout=1.5)

            step_a = (step_a + 1) % len(path_a)
            step_b = (step_b + 1) % len(path_b)

        except Exception as e:
            # Silently retry on connection blip
            pass

        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_simulator()
