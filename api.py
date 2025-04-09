from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.sensor import SensorData, SensorSummary, SystemHealth
from typing import List
import sqlite3
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import os
import psutil
import shutil
import platform
import time
import subprocess
import socket

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
API_PORT = int(os.getenv("API_PORT", 8000))
API_TITLE = os.getenv("API_TITLE", "BQCam Sensor API – BMP280")

app = FastAPI(
    title=API_TITLE,
    description="""
Secure REST API for the BQCam system, designed to collect and serve environmental data
from a BMP280 sensor connected to a Raspberry Pi.

This API powers the BQCam dashboard and exposes both sensor readings and system health metrics.

### Main Features:
- 🌡️ Get the latest sensor data (`/latest`)
- 🕓 Query historical or daily data (`/history`, `/range`)
- 📈 Generate summaries with min/max/avg (`/summary`)
- ⚙️ Monitor Raspberry Pi system health (`/health`)  
  (includes disk, RAM, CPU usage, temperature, uptime)

### Authentication:
All endpoints require Bearer Token authentication. .env -> API_TOKEN=supersecrettoken

### Notes:
- Dates must be in the format `YYYY-MM-DD`
- Ideal for lightweight monitoring and camera integrations on Raspberry Pi Zero 2 W
- Designed to run alongside the BQCam web dashboard on the same host

### Tech Stack:
FastAPI · SQLite · psutil · BMP280 · Raspberry Pi
""",
    version="1.2.0"
)

# Ajout CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou spécifie ["http://bqcam03"] si tu veux limiter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def get_cpu_temperature():
    try:
        output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(output.replace("temp=", "").replace("'C\n", ""))
    except:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                raw = f.read()
            return round(int(raw) / 1000, 1)
        except:
            return None


def get_local_ip():
    try:
        # On ouvre une socket UDP vers une IP externe sans envoyer de paquets
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"


def get_uptime():
    return time.time() - psutil.boot_time()


def check_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")


def get_db_connection():
    return sqlite3.connect("sensor_data.db")


@app.get("/latest", response_model=SensorData, dependencies=[Depends(check_token)])
def get_latest():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "timestamp": row[0],
            "temperature": row[1],
            "pressure": row[2]
        }
    else:
        raise HTTPException(status_code=404, detail="No data found")


@app.get("/history", response_model=List[SensorData], dependencies=[Depends(check_token)])
def get_history(limit: int = 10):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM measurements ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()

    return [
        {"timestamp": row[0], "temperature": row[1], "pressure": row[2]}
        for row in rows
    ]


@app.get("/range", response_model=List[SensorData], dependencies=[Depends(check_token)])
def get_range(start: str, end: str):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in format YYYY-MM-DD")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM measurements
        WHERE date(timestamp) BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start, end))
    rows = cur.fetchall()
    conn.close()

    return [
        {"timestamp": row[0], "temperature": row[1], "pressure": row[2]}
        for row in rows
    ]


@app.get("/summary", response_model=SensorSummary, dependencies=[Depends(check_token)])
def get_summary(start: str, end: str):
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in format YYYY-MM-DD")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            MIN(temperature), MAX(temperature), AVG(temperature),
            MIN(pressure), MAX(pressure), AVG(pressure)
        FROM measurements
        WHERE date(timestamp) BETWEEN ? AND ?
    """, (start, end))
    row = cur.fetchone()
    conn.close()

    return {
        "temperature": {
            "min": round(row[0], 2),
            "max": round(row[1], 2),
            "avg": round(row[2], 2)
        },
        "pressure": {
            "min": round(row[3], 2),
            "max": round(row[4], 2),
            "avg": round(row[5], 2)
        }
    }


@app.get("/health", response_model=SystemHealth, dependencies=[Depends(check_token)])
def health_check():
    try:
        # Disk
        disk = shutil.disk_usage("/")
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        disk_free_gb = round(disk.free / (1024 ** 3), 2)

        # RAM
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024 ** 2), 1)
        ram_used = round(ram.used / (1024 ** 2), 1)
        ram_available = round(ram.available / (1024 ** 2), 1)

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_temp = get_cpu_temperature()

        return {
            "status": "ok",
            "ip": get_local_ip(),
            "hostname": socket.gethostname(),
            "uptime_sec": int(get_uptime()),
            "disk": {
                "used_gb": disk_used_gb,
                "free_gb": disk_free_gb,
                "total_gb": disk_total_gb
            },
            "ram": {
                "used_mb": ram_used,
                "available_mb": ram_available,
                "total_mb": ram_total
            },
            "cpu": {
                "percent": cpu_percent,
                "temp_c": cpu_temp
            },
            "platform": platform.platform()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=API_PORT, reload=False)
