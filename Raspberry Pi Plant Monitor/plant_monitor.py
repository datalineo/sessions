# ---------------------------------
# This script reads the moisture value from a Raspberry Pi Sensor, add current weather 
# conditions and sends to Azure IoT Hub
# ---------------------------------

import time
import grovepi
import requests
import picamera
from configparser import ConfigParser
from azure.iot.device import IoTHubDeviceClient, Message
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from di_sensors.easy_temp_hum_press import EasyTHPSensor
import json
import datetime

# ---------------------------------
# Set local variables
# ---------------------------------
moisture_sensor_port = 0
capture_date = datetime.datetime.now()

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
storage_connection_string=config.get('azure-storage','storage_connection_string')
storage_container=config.get('azure-storage','container')
img_file_name_fixed = 'plant_monitor_current.jpg'

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
# Azure Blob service client
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

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
        #print('moisture:',soil_moisture)

        # -----------------------------------
        # Capture te image & save to Azure blob
        # -----------------------------------
        img_file_name_timestamp = 'image_{0}.jpg'.format(now.strftime('%Y%m%d_%H%M%S'))

        capture_diff = now - capture_date
        if now.hour == 12 and capture_diff.days > 0:
            camera = picamera.PiCamera()
            camera.resolution = (640,480)
            # allow th camer to warm up & focus
            time.sleep(2)
            camera.capture(img_file_name_fixed)
            camera.close()
            capture_date = datetime.datetime.now()

        # overwrite the image used for power BI reports
        fixed_blob_client = blob_service_client.get_blob_client(container=storage_container,blob=img_file_name_fixed)
        with open(img_file_name_fixed,'rb') as fixxy:
            fixed_blob_client.upload_blob(fixxy,overwrite=True)

        # create timestamped version, for potential time-lapse views 
        timestamp_blob_client = blob_service_client.get_blob_client(container=storage_container,blob=img_file_name_timestamp)
        with open(img_file_name_fixed,'rb') as stampy:
            timestamp_blob_client.upload_blob(stampy,overwrite=True)

        print('mesage sent...',now.strftime('%Y-%m-%d %H:%M:%S'))
        time.sleep(900)

    except KeyboardInterrupt:
        print ('Session ended by user')
        break
    except IOError as io_error:
        print (io_error)


