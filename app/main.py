from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.init_db import init_db
from app.api.api_router import api_router
from app.services.mqtt_service import mqtt_subscriber

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    
    mqtt_subscriber.start()
    yield
    mqtt_subscriber.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full Stack GPS-based Vehicle Tracking System API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "message": "GPS Vehicle Tracking System API is online and operational",
        "docs_url": "/docs",
        "version": settings.VERSION
    }

HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniTrack Pro - Ultra-Smooth GPS Fleet Tracking</title>
  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <!-- Google Fonts & Font Awesome Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <style>
    :root {
      --bg-dark: #0B0F17;
      --card-bg: #111827;
      --card-border: #1F2937;
      --primary: #3B82F6;
      --accent-cyan: #06B6D4;
      --accent-green: #10B981;
      --accent-amber: #F59E0B;
      --text-main: #F9FAFB;
      --text-muted: #9CA3AF;
      --text-sub: #6B7280;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body { background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; }

    header {
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      padding: 12px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      font-weight: 800;
      font-size: 1.25rem;
      letter-spacing: -0.5px;
    }
    .brand-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: linear-gradient(135deg, #2563EB, #06B6D4);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      box-shadow: 0 0 15px rgba(37, 99, 235, 0.5);
    }
    .brand-badge {
      background: rgba(59, 130, 246, 0.15);
      color: #60A5FA;
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
    }

    .status-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 6px 14px;
      border-radius: 30px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--accent-green);
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 8px var(--accent-green);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse { 0% { transform: scale(0.9); opacity: 0.8; } 50% { transform: scale(1.4); opacity: 1; } 100% { transform: scale(0.9); opacity: 0.8; } }

    .btn {
      padding: 8px 16px;
      border-radius: 10px;
      border: none;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.85rem;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
    }
    .btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-main); }
    .btn-outline:hover { background: #1F2937; }
    .btn-primary { background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; }
    .btn-accent { background: linear-gradient(135deg, #F59E0B, #D97706); color: white; }

    .app-layout {
      display: grid;
      grid-template-columns: 410px 1fr;
      gap: 20px;
      padding: 20px 28px;
      flex: 1;
      max-width: 1750px;
      margin: 0 auto;
      width: 100%;
    }

    .sidebar { display: flex; flex-direction: column; gap: 18px; }

    .glass-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .card-label {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.8px;
      text-transform: uppercase;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .auth-banner {
      background: linear-gradient(135deg, #1E3A8A, #172554);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 14px;
    }
    .auth-header { display: flex; align-items: center; gap: 12px; }
    .avatar {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #3B82F6, #8B5CF6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.1rem;
    }

    .user-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .user-tab {
      background: #1A2234;
      border: 1.5px solid #283548;
      border-radius: 12px;
      padding: 12px;
      cursor: pointer;
      transition: all 0.25s;
      text-align: left;
    }
    .user-tab.active {
      border-color: var(--primary);
      background: rgba(37, 99, 235, 0.15);
      box-shadow: 0 0 16px rgba(37, 99, 235, 0.2);
    }
    .user-tab .tab-title { font-weight: 700; font-size: 0.88rem; color: var(--text-main); }
    .user-tab .tab-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }

    .telemetry-hud {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 12px;
      margin: 14px 0;
    }
    .hud-box {
      background: #182234;
      border: 1px solid #233044;
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      position: relative;
    }
    .hud-box .val {
      font-size: 1.65rem;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
      color: #60A5FA;
      margin-top: 4px;
    }
    .hud-box .unit { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; }

    .compass-dial {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: 2px dashed #3B82F6;
      display: flex;
      align-items: center;
      justify-content: center;
      position: absolute;
      right: 12px;
      top: 14px;
    }
    .compass-needle { color: var(--accent-amber); transition: transform 0.8s ease-out; }

    .stops-timeline { max-height: 190px; overflow-y: auto; padding-right: 6px; margin-top: 10px; }
    .stops-timeline::-webkit-scrollbar { width: 5px; }
    .stops-timeline::-webkit-scrollbar-thumb { background: #374151; border-radius: 10px; }

    .timeline-item { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; position: relative; }
    .timeline-item::before { content: ''; position: absolute; left: 7px; top: 22px; bottom: -6px; width: 2px; background: #283548; }
    .timeline-item:last-child::before { display: none; }
    .timeline-dot { width: 16px; height: 16px; border-radius: 50%; background: #3B82F6; border: 3px solid var(--card-bg); margin-top: 2px; flex-shrink: 0; z-index: 2; }
    .timeline-dot.origin { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
    .timeline-dot.dest { background: #EF4444; box-shadow: 0 0 8px #EF4444; }
    .timeline-text { flex: 1; }
    .timeline-name { font-size: 0.82rem; font-weight: 600; color: var(--text-main); }
    .timeline-desc { font-size: 0.72rem; color: var(--text-muted); }

    .map-wrapper {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 8px 30px rgba(0,0,0,0.3);
      position: relative;
    }
    .map-header {
      padding: 14px 20px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(17, 24, 39, 0.9);
      backdrop-filter: blur(8px);
      z-index: 10;
    }
    #map { flex: 1; width: 100%; min-height: 580px; z-index: 1; background: #0B0F17; }

    /* Custom Leaflet Marker with Smooth CSS Animation */
    .custom-bus-marker {
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: transform 1.5s cubic-bezier(0.25, 1, 0.5, 1);
    }
    .bus-ring {
      position: absolute;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: rgba(59, 130, 246, 0.35);
      animation: busPulse 2s infinite ease-out;
    }
    @keyframes busPulse {
      0% { transform: scale(0.6); opacity: 1; }
      100% { transform: scale(1.8); opacity: 0; }
    }
    .bus-core {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #3B82F6, #1D4ED8);
      border: 2px solid white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 15px;
      box-shadow: 0 4px 14px rgba(0,0,0,0.5);
      z-index: 3;
    }
    .bus-heading-arrow {
      position: absolute;
      top: -12px;
      color: #F59E0B;
      font-size: 14px;
      text-shadow: 0 2px 4px rgba(0,0,0,0.6);
      transition: transform 0.6s ease;
    }

    .leaflet-marker-icon {
      transition: all 1.8s linear;
    }
  </style>
</head>
<body>

<header>
  <div class="brand">
    <div class="brand-icon">
      <i class="fa-solid fa-bus-simple"></i>
    </div>
    <div>
      <span>OmniTrack Pro</span>
      <span class="brand-badge">Accurate Route Telemetry</span>
    </div>
  </div>

  <div class="nav-actions">
    <div class="status-pill">
      <span class="pulse-dot"></span>
      <span>Smooth GPS Stream Active</span>
    </div>
    <a href="/docs" target="_blank" class="btn btn-outline">
      <i class="fa-solid fa-code"></i> OpenAPI Docs
    </a>
  </div>
</header>

<div class="app-layout">
  <div class="sidebar">

    <div class="glass-card">
      <div class="card-label">
        <span>Active User Session</span>
        <span style="color:#34D399; font-weight:700;"><i class="fa-solid fa-shield-halved"></i> Enforced Isolation</span>
      </div>

      <div class="auth-banner">
        <div class="auth-header">
          <div class="avatar" id="userAvatar">A</div>
          <div>
            <h3 id="currentUserName" style="font-size:1.05rem; font-weight:700;">User A (North Commuter)</h3>
            <p id="currentUserSub" style="font-size:0.75rem; color:#93C5FD;">Assigned: Route A & BUS-001</p>
          </div>
        </div>
      </div>

      <div class="user-tabs">
        <button class="user-tab active" id="tabUserA" onclick="switchUser('usera')">
          <div class="tab-title"><i class="fa-solid fa-user-check"></i> User A</div>
          <div class="tab-sub">Route A • BUS-001</div>
        </button>
        <button class="user-tab" id="tabUserB" onclick="switchUser('userb')">
          <div class="tab-title"><i class="fa-solid fa-user-check"></i> User B</div>
          <div class="tab-sub">Route B • BUS-002</div>
        </button>
      </div>
    </div>

    <div class="glass-card">
      <div class="card-label">
        <span>Assigned Vehicle Telemetry</span>
        <span id="badgeStatus" class="status-pill" style="padding:2px 10px; font-size:0.7rem;">IN_TRANSIT</span>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
          <h2 id="vehNumber" style="font-size:1.55rem; font-weight:800; color:#60A5FA;">BUS-001</h2>
          <p id="vehModel" style="font-size:0.8rem; color:var(--text-muted);">Volvo 9700 EV</p>
        </div>
        <button class="btn btn-accent" style="padding:6px 12px; font-size:0.78rem;" onclick="advanceStep()">
          <i class="fa-solid fa-forward-step"></i> Next Step
        </button>
      </div>

      <div class="telemetry-hud">
        <div class="hud-box">
          <span class="unit"><i class="fa-solid fa-gauge-high"></i> ACCURATE SPEED</span>
          <div class="val" id="hudSpeed">38.5 <span style="font-size:0.9rem; font-weight:500;">km/h</span></div>
        </div>
        <div class="hud-box">
          <span class="unit"><i class="fa-solid fa-compass"></i> HEADING</span>
          <div class="val" id="hudHeading">210°</div>
          <div class="compass-dial">
            <i class="fa-solid fa-location-arrow compass-needle" id="compassNeedle"></i>
          </div>
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; font-size:0.76rem; color:var(--text-muted); padding:4px 2px;">
        <span id="hudCoords"><i class="fa-solid fa-location-dot"></i> 13.0827, 80.2707</span>
        <span id="hudPing"><i class="fa-regular fa-clock"></i> Ping: 1s ago</span>
      </div>
    </div>

    <div class="glass-card">
      <div class="card-label">
        <span>Scheduled Bus Stops</span>
        <span id="stopsCount" style="color:var(--primary); font-weight:700;">10 Stops</span>
      </div>

      <h3 id="routeName" style="font-size:1rem; font-weight:700; color:var(--text-main);">Route A (North Express)</h3>
      <div class="stops-timeline" id="stopsTimeline"></div>
    </div>

  </div>

  <div class="map-wrapper">
    <div class="map-header">
      <div>
        <h3 style="font-size:1.05rem; font-weight:700;"><i class="fa-solid fa-map-location-dot" style="color:var(--primary); margin-right:8px;"></i> Live Smooth Navigation Route Map</h3>
        <p style="font-size:0.76rem; color:var(--text-muted);">Vehicle glides accurately along the scheduled bus route without jumping</p>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-outline" style="font-size:0.78rem;" onclick="fitRouteBounds()">
          <i class="fa-solid fa-expand"></i> Fit Route
        </button>
        <button class="btn btn-primary" style="font-size:0.78rem;" onclick="centerOnVehicle()">
          <i class="fa-solid fa-crosshairs"></i> Target Vehicle
        </button>
      </div>
    </div>
    <div id="map"></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  let currentUsername = 'usera';
  let token = '';
  let map = null;
  let vehicleMarker = null;
  let routePolyline = null;
  let stopMarkers = [];
  let pollInterval = null;
  let assignedVehicleId = 1;

  async function login(username) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: 'password123' })
    });
    const data = await res.json();
    token = data.access_token;
    return token;
  }

  async function initDashboard() {
    await login(currentUsername);
    await loadRouteAndVehicle();
    await updateLiveLocation();

    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(updateLiveLocation, 2000);
  }

  async function switchUser(user) {
    currentUsername = user;
    document.getElementById('tabUserA').classList.toggle('active', user === 'usera');
    document.getElementById('tabUserB').classList.toggle('active', user === 'userb');

    document.getElementById('userAvatar').innerText = user === 'usera' ? 'A' : 'B';
    document.getElementById('currentUserName').innerText = user === 'usera' ? 'User A (North Commuter)' : 'User B (South Commuter)';
    document.getElementById('currentUserSub').innerText = user === 'usera' ? 'Assigned: Route A & BUS-001' : 'Assigned: Route B & BUS-002';

    if (vehicleMarker && map) {
      map.removeLayer(vehicleMarker);
      vehicleMarker = null;
    }

    await initDashboard();
  }

  async function loadRouteAndVehicle() {
    // Fetch Route
    const routeRes = await fetch('/api/user/assigned-route', { headers: { 'Authorization': `Bearer ${token}` } });
    const route = await routeRes.json();

    document.getElementById('routeName').innerText = route.route_name;
    document.getElementById('stopsCount').innerText = `${route.waypoints.length} Points`;

    const timeline = document.getElementById('stopsTimeline');
    timeline.innerHTML = '';
    const latlngs = [];

    stopMarkers.forEach(m => map && map.removeLayer(m));
    stopMarkers = [];

    route.waypoints.forEach((wp, idx) => {
      latlngs.push([wp.latitude, wp.longitude]);
      const isFirst = idx === 0;
      const isLast = idx === route.waypoints.length - 1;

      const item = document.createElement('div');
      item.className = 'timeline-item';
      item.innerHTML = `
        <div class="timeline-dot ${isFirst ? 'origin' : isLast ? 'dest' : ''}"></div>
        <div class="timeline-text">
          <div class="timeline-name">${wp.name} ${wp.is_stop ? '<span style="color:#60A5FA; font-size:0.7rem;">• Stop</span>' : ''}</div>
          <div class="timeline-desc">${wp.latitude.toFixed(4)}, ${wp.longitude.toFixed(4)}</div>
        </div>
      `;
      timeline.appendChild(item);

      if (map) {
        const marker = L.circleMarker([wp.latitude, wp.longitude], {
          radius: isFirst || isLast ? 7 : 4.5,
          color: isFirst ? '#10B981' : isLast ? '#EF4444' : '#3B82F6',
          fillColor: isFirst ? '#10B981' : isLast ? '#EF4444' : '#3B82F6',
          fillOpacity: 0.95,
          weight: 2
        }).bindPopup(`<b>${wp.name}</b><br>${isFirst ? 'Origin Point' : isLast ? 'Destination Terminus' : 'Scheduled Bus Stop'}`).addTo(map);
        stopMarkers.push(marker);
      }
    });

    // Fetch Vehicle
    const vehRes = await fetch('/api/user/assigned-vehicle', { headers: { 'Authorization': `Bearer ${token}` } });
    const veh = await vehRes.json();
    assignedVehicleId = veh.id;
    document.getElementById('vehNumber').innerText = veh.vehicle_number;
    document.getElementById('vehModel').innerText = veh.model;

    // Draw route polyline
    if (map) {
      if (routePolyline) map.removeLayer(routePolyline);
      routePolyline = L.polyline(latlngs, {
        color: '#3B82F6',
        weight: 6,
        opacity: 0.8,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);
      map.fitBounds(routePolyline.getBounds(), { padding: [40, 40] });
    }
  }

  async function updateLiveLocation() {
    try {
      const res = await fetch('/api/tracking/current', { headers: { 'Authorization': `Bearer ${token}` } });
      if (!res.ok) return;
      const loc = await res.json();

      document.getElementById('hudSpeed').innerHTML = `${loc.speed.toFixed(1)} <span style="font-size:0.85rem; font-weight:500;">km/h</span>`;
      document.getElementById('hudHeading').innerText = `${loc.heading.toFixed(0)}°`;
      document.getElementById('compassNeedle').style.transform = `rotate(${loc.heading}deg)`;
      document.getElementById('hudCoords').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`;
      document.getElementById('hudPing').innerHTML = `<i class="fa-regular fa-clock"></i> ${new Date().toLocaleTimeString()}`;
      document.getElementById('badgeStatus').innerText = loc.status;

      // Update vehicle marker with smooth transition
      if (map && loc.latitude && loc.longitude) {
        const latlng = [loc.latitude, loc.longitude];
        if (!vehicleMarker) {
          const busHtml = `
            <div class="custom-bus-marker">
              <div class="bus-ring"></div>
              <div class="bus-core"><i class="fa-solid fa-bus"></i></div>
            </div>
          `;
          const customIcon = L.divIcon({
            html: busHtml,
            className: '',
            iconSize: [48, 48],
            iconAnchor: [24, 24]
          });
          vehicleMarker = L.marker(latlng, { icon: customIcon }).addTo(map);
        } else {
          vehicleMarker.setLatLng(latlng);
        }
      }
    } catch (e) {
      console.error(e);
    }
  }

  function centerOnVehicle() {
    if (vehicleMarker) {
      map.setView(vehicleMarker.getLatLng(), 15, { animate: true });
    }
  }

  function fitRouteBounds() {
    if (routePolyline) {
      map.fitBounds(routePolyline.getBounds(), { padding: [40, 40], animate: true });
    }
  }

  async function advanceStep() {
    await fetch(`/api/gps/simulate-step/${assignedVehicleId}`, { method: 'POST' });
    await updateLiveLocation();
  }

  window.onload = () => {
    map = L.map('map', { zoomControl: false }).setView([13.0827, 80.2707], 13);
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors, © CARTO'
    }).addTo(map);

    initDashboard();
  };
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def root_ui():
    return HTML_UI
