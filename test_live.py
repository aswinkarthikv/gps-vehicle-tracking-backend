import requests
import time

res = requests.post("http://localhost:8000/api/auth/login", json={"username": "usera", "password": "password123"}).json()
token = res["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== 1. Logged in as User A ===")
route = requests.get("http://localhost:8000/api/user/assigned-route", headers=headers).json()
print("Assigned Route:", route["route_name"], f"({len(route['waypoints'])} waypoints)")

veh = requests.get("http://localhost:8000/api/user/assigned-vehicle", headers=headers).json()
print("Assigned Vehicle:", veh["vehicle_number"], f"[{veh['model']}]")

print("\n=== 2. Live GPS Telemetry Stream (Live Updates) ===")
for i in range(3):
    track = requests.get("http://localhost:8000/api/tracking/current", headers=headers).json()
    print(f"Ping {i+1}: Lat={track['latitude']}, Lng={track['longitude']} | Speed={track['speed']} km/h | Status={track['status']}")
    time.sleep(3)

print("\n=== 3. Strict Authorization Check ===")
unauth_resp = requests.get("http://localhost:8000/api/vehicles/2/current-location", headers=headers)
print(f"User A trying to access Vehicle 2 -> Status: {unauth_resp.status_code} ({unauth_resp.json()['detail']})")
