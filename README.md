# 📷 BQCam – Sensor & Stream Dashboard for Raspberry Pi Zero 2 W

BQCam is a lightweight, FastAPI-powered dashboard for real-time monitoring of a BMP280 sensor (temperature & pressure),
system health, and camera streaming — built specifically for Raspberry Pi Zero 2 W.

---

## 📦 Project Structure

```
bqcam-dashboard/
├── .env                   # Environment config (API keys, ports, URLs)
├── api.py                # FastAPI REST API (sensor + system health)
├── webapp.py             # FastAPI-powered dashboard (serves UI)
├── sensor_data.db        # SQLite database (auto-generated)
├── static/               # CSS, JS assets for dashboard
├── templates/            # Jinja2 HTML templates
├── venv/                 # Python virtual environment
└── systemd/              # systemd service files (optional)
```

---

## 🚀 Features

- 🌡 Sensor data from BMP280 (I2C) – /latest, /history, /range, /summary
- ⚙️ System health endpoint – disk, RAM, CPU usage & temperature, uptime, IP, hostname
- 📊 Realtime dashboard (Chart.js + Log view)
- 🔐 API secured with Static Bearer Token (API_TOKEN)
- 🎥 Embedded camera stream with MediaMTX
- 🧠 Clean FastAPI structure + responsive cyber-styled UI

---

## 🧪 Requirements

```
- Raspberry Pi Zero 2 W or other Raspberry Pi
- I'm actually on Bullseye Lite (headless)
- BMP280 sensor (connected via I2C)
- Python ≥ 3.9
- Optional: camera stream served via MediaMTX with WebRTC enabled, actually on same Pi for me
```

---

## ⚙️ Setup Instructions

### 1. Clone the project & create a virtualenv

```shell
git clone git@github.com:BugQuest/BQCam-Dashboard.git
cd BQCam-Dashboard
python3 -m venv venv
source venv/bin/activate # if you want to test it locally
```

### 2. Install Python dependencies

```shell
pip install -r requirements.txt
```

Or manually:

```shell
pip install fastapi uvicorn python-dotenv psutil adafruit-circuitpython-bmp280
```

> Plus: adafruit-blinka, adafruit-circuitpython-busdevice, RPi.GPIO, etc. (installed automatically via pip on Pi OS)

---

### 3. Create your `.env` file

```dotenv
API_TOKEN=supersecrettoken  
API_PORT=8698  
API_URL=http://<raspberry-ip>:<API_PORT>

WEB_PORT=8080  
CAM_URL=http://<raspberry-ip>:<port>/<cam>
#or
CAM_URL=http://<login>:<pass>@<raspberry-ip>:<port>/<cam>
```

---

### 4. Run the services (API + Dashboard)

#### a. API service

uvicorn api:app --host 0.0.0.0 --port $API_PORT

#### b. Dashboard (web frontend)

uvicorn webapp:app --host 0.0.0.0 --port $WEB_PORT

---

### 5. [Optional] Set up systemd services

Create the following files in `/etc/systemd/system/`:  
Change paths and permissions accordingly to your setup.

> example: sudo nano /etc/systemd/system/bqcam-api.service

#### bqcam-api.service

```
[Unit]  
Description=BQCam API (Sensor + System)  
After=network.target

[Service]  
User=pi  
WorkingDirectory=/home/pi/BQCam-Dashboard  
Environment="PATH=/home/pi/BQCam-Dashboard/venv/bin"  
EnvironmentFile=/home/pi/BQCam-Dashboard/.env  
ExecStart=/home/pi/BQCam-Dashboard/venv/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port ${API_PORT}  
Restart=always

[Install]  
WantedBy=multi-user.target
```

#### bqcam-web.service

```
[Unit]  
Description=BQCam Dashboard (Web UI)  
After=network.target

[Service]  
User=pi  
WorkingDirectory=/home/pi/BQCam-Dashboard  
Environment="PATH=/home/pi/BQCam-Dashboard/venv/bin"  
EnvironmentFile=/home/pi/BQCam-Dashboard/.env  
ExecStart=/home/pi/BQCam-Dashboard/venv/bin/python3 -m uvicorn webapp:app --host 0.0.0.0 --port ${WEB_PORT}  
Restart=always

[Install]  
WantedBy=multi-user.target
```

Then:

```shell
sudo systemctl daemon-reload  
sudo systemctl enable bqcam-api bqcam-web  
sudo systemctl start bqcam-api bqcam-web
```

---

## 📡 Camera Streaming – MediaMTX

This project expects a stream to be available at:

```
 exemple: http://<raspberry-ip>:<port>/<cam>  
 exemple: http://<login>:<pass>@<raspberry-ip>:<port>/<cam>
```

This is served by MediaMTX or similar WebRTC relay service.  
It's just an iframe integrated to the dashboard.

---

## 📡 API Overview

- GET /latest — latest sensor measurement
- GET /history?limit=30 — recent N entries
- GET /range?start=YYYY-MM-DD&end=YYYY-MM-DD — range
- GET /summary?start=...&end=... — min/max/avg
- GET /health — Raspberry Pi system health

All endpoints require:

Authorization: Bearer <API_TOKEN>

---

## 📺 Dashboard Access

Accessible at:

```
http://<raspberry-ip>:<WEB_PORT>/
```

Includes:

- Live dual-axis graph (Temp & Pressure)
- Live Raspberry Pi stats (CPU, RAM, Disk, Temp)
- Log feed
- Embedded stream (via iframe)
- Circular refresh indicators

---

## 🧼 To Do / Ideas

- Export CSV/JSON data
- Threshold alerts (high CPU temp / sensor triggers)
- Multi-cam support (bqcam01, bqcam02…)
- External push to cloud or MQTT

---

## 🛡 License

MIT – designed for self-hosted IoT dashboards.
