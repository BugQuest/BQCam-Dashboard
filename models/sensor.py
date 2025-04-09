from pydantic import BaseModel
from typing import Optional


class SensorData(BaseModel):
    timestamp: str
    temperature: float
    pressure: float

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-04-09 00:05:31",
                "temperature": 18.39,
                "pressure": 963.79
            }
        }


class SensorSummary(BaseModel):
    temperature: dict
    pressure: dict

    class Config:
        schema_extra = {
            "example": {
                "temperature": {
                    "min": 17.16,
                    "max": 20.63,
                    "avg": 18.21
                },
                "pressure": {
                    "min": 962.19,
                    "max": 963.95,
                    "avg": 963.41
                }
            }
        }


class SystemHealth(BaseModel):
    status: str
    hostname: str
    ip: str
    uptime_sec: int
    disk: dict
    ram: dict
    cpu: dict
    platform: str

    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "hostname": "bqcam03",
                "ip": "192.168.1.23",
                "uptime_sec": 84599,
                "disk": {
                    "used_gb": 4.2,
                    "free_gb": 23.8,
                    "total_gb": 28.0
                },
                "ram": {
                    "used_mb": 435.2,
                    "available_mb": 132.5,
                    "total_mb": 512.0
                },
                "cpu": {
                    "percent": 12.5,
                    "temp_c": 47.3
                },
                "platform": "Linux-6.1.21-v7+-armv7l-with-glibc2.31"
            }
        }
