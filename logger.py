import time
import sqlite3
import board
import busio
from adafruit_bmp280 import Adafruit_BMP280_I2C

# Initialisation I2C
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = Adafruit_BMP280_I2C(i2c, address=0x76)

# Connexion SQLite
conn = sqlite3.connect("sensor_data.db")
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS measurements (
    timestamp TEXT,
    temperature REAL,
    pressure REAL
)''')

# Lecture
now = time.strftime('%Y-%m-%d %H:%M:%S')
cur.execute("INSERT INTO measurements VALUES (?, ?, ?)", (
    now,
    round(bmp280.temperature, 2),
    round(bmp280.pressure, 2)
))

conn.commit()
conn.close()
