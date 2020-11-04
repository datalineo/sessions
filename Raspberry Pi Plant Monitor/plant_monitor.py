# ---------------------------------
# This script reads the moisture value from a Raspberry Pi Sensor, add current weather 
# conditions and sends to Azure IoT Hub
# ---------------------------------

import time
import grovepi
import requests
from configparser import ConfigParser
from azure.iot.device import IoTHubDeviceClient, Message
from di_sensors.easy_temp_hum_press import EasyTHPSensor
import json
import datetime

# ---------------------------------
# Set local variables
# ---------------------------------
moisture_sensor_port = 0


# ---------------------------------
# Get configuration settings
# ---------------------------------

config_file = '/home/pi/GIT/config/config_moisture.ini'
config=ConfigParser()
config.read(config_file)

endpoint = config.get('openweathermap','endpoint')
api_key = config.get('openweathermap','api_key')
location = config.get('openweathermap','location')
units = config.get('openweathermap','units')
iot_connection_string = config.get('azure-iot','iot-connection-string')

# ---------------------------------
# Set structure for IoT message
# ---------------------------------

iot_text = '{{"moisture": {moisture},"weather":{humidity}}}'
url = '{0}?q={1}&appid={2}&units={3}'.format(endpoint,location,api_key,units)


# ---------------------------------
# Initiate API and IoT and sensor sessions
# ---------------------------------
# API sssion
session = requests.session()
# IoT session
iot_client = IoTHubDeviceClient.create_from_connection_string(iot_connection_string)
# THP sensor
thp_sensor = EasyTHPSensor()

while True:
    try:
        now = datetime.datetime.now()
        # Get the moisture sensor reading
        soil_moisture = grovepi.analogRead(moisture_sensor_port)
        # Get the Temp/Humidity/Pressure sensor readings
        inside_temp = thp_sensor.safe_celsius()
        inside_humidity = thp_sensor.safe_humidity()
        inside_pressure = thp_sensor.safe_pressure()
        # Get the outside weather data from API service
        response = session.get(url)
        iot_message_json = response.json()
        # Add the sensor & date info to the API response
        iot_message_json['capturedate']=now.strftime('%Y-%m-%d %H:%M:%S')
        iot_message_json['soil_moisture']=soil_moisture
        iot_message_json['inside_temp']=inside_temp
        iot_message_json['inside_humidity']=inside_humidity
        iot_message_json['inside_pressure']=inside_pressure
        iot_message = Message(json.dumps(iot_message_json))
        #print(iot_message)
        iot_client.send_message(iot_message)
        print('mesage sent...',now.strftime('%Y-%m-%d %H:%M:%S'))
        #print('moisture:',soil_moisture)
        time.sleep(300)

    except KeyboardInterrupt:
        print ('Session ended by user')
        break
    except IOError:
        print ("Error")
        exit()
