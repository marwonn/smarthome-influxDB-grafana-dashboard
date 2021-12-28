import time
import Adafruit_DHT

from helper.config import Config
from influxdb import InfluxDBClient

# Initialize DHT22 sensor
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# InfluxDB settings
host = Config.HOST_IP           # IP address of host to connect to. 
port = Config.HOST_PORT         # influxDB port, typically '8086'
user = Config.DB_USER           # if not set, default user is 'admin'.
password = Config.DB_PASSWORD   # default password for admin is empty string ''.
dbname = "dht22-4b"             # database name. DB needs to be creaated first via influx command line.

client = InfluxDBClient(host=host, port=port)
client.switch_database('dht22-4b')

measurement = "dht22-4b"
location = "pantry"
device = "Raspi-4B"

# Read the sensor using the configured driver and gpio
humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

# I guess this step is not really necessary. InfluxDB should create timestamp on it's own. # TODO
current_time = time.gmtime()
timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', current_time)

# Create JSON
data = [
    {
        "measurement": measurement,
        "tags": {
            "location": location,
            "device": device
        },
        "time": timestamp,
        "fields": {
            "temperature": temperature, 
            "humidity": humidity
            },
    }
]
# Send the JSON data to InfluxDB
client.write_points(data)
