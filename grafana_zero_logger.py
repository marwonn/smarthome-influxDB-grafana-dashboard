import time
import requests
import aqi
import Adafruit_DHT

from influxdb import InfluxDBClient
from helper.sdss011_class import SDS011
from helper.config import Config

'''
the sdss011_class is copied from https://github.com/ikalchev/py-sds011.
Using this class makes much easier to send the sensor into sleep mode and 
get the sensor data. @thanks to ikalchev.
'''

# SDS001 Sensor Interface
sensor = SDS011("/dev/ttyUSB0", use_query_mode=True)

# DHT22 Sensor Interface
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# Influx DB Settings
host = Config.HOST_IP
port = Config.HOST_PORT
user = Config.DB_USER
password = Config.DB_PASSWORD
dbname = 'dht22zero'

client = InfluxDBClient(host=host, port=port)
client.switch_database('dht22zero')

measurement = "dht22zero"
location = "mobil"
device = "Raspi-Zero"

# Get OUTDOOR pmt 10 and pmt 2.5 from https://maps.sensor.community/ & calculate the aqi
SENSOR_OUTDOOR_ID = Config.OUTDOOR_SENSOR_ID        # takes an ID from maps.sensor.community

r = requests.get(f'http://data.sensor.community/airrohr/v1/sensor/{SENSOR_OUTDOOR_ID}/')

pm10_outdoor = float(r.json()[0]['sensordatavalues'][0]['value'])
pm25_outdoor = float(r.json()[0]['sensordatavalues'][1]['value'])

aqi_outdoor = aqi.to_aqi([
    (aqi.POLLUTANT_PM25, pm25_outdoor),
    (aqi.POLLUTANT_PM10, pm10_outdoor)
    ])

# Read the sensor using the configured driver and gpio
humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

# Read SDS001 Sensor data & calculate Air Quality Index
sensor.sleep(sleep=False)
time.sleep(30)
pmt25, pmt10 = sensor.query()
sensor.sleep()

myaqi = aqi.to_aqi([
    (aqi.POLLUTANT_PM25, pmt25),
    (aqi.POLLUTANT_PM10, pmt10)
    ])

# Write aqi to a text file. Only needed for the display.py. Cannot directly be displayed on the display.
with open('./aqi.txt', 'w') as f:
    f.write(str(myaqi))
    f.close()
    
current_time = time.gmtime()
timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', current_time)

# Create the JSON data structure
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
                    "humidity": humidity,
                    "pmt25": pmt25,
                    "pmt10": pmt10,
                    "aqi": myaqi,
                    "aqi_sinnersdorf": aqi_outdoor
                    },
            }
        ]

# Send the JSON data to InfluxDB
client.write_points(data)
