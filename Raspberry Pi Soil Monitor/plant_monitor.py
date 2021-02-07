# ---------------------------------
# This script reads the moisture value from a Raspberry Pi Sensor, add current weather 
# conditions and sends to Power BI Streaming & Azure storage
# ---------------------------------

import time
import grovepi
import requests
import picamera
from configparser import ConfigParser
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from di_sensors.easy_temp_hum_press import EasyTHPSensor
import json
import datetime
import uuid

# ---------------------------------
# Set local variables
# ---------------------------------
moisture_sensor_port = 0
capture_date = datetime.datetime.now()
today_string = capture_date.strftime("%Y-%m-%d")

# ---------------------------------
# Get configuration settings
# ---------------------------------

config_file = '/home/pi/GIT/config/config_moisture.ini'
config=ConfigParser()
config.read(config_file)

openweather_endpoint = config.get('openweathermap','endpoint')
openweather_api_key = config.get('openweathermap','api_key')
openweather_location = config.get('openweathermap','location')
openweather_units = config.get('openweathermap','units')
img_storage_connection_string=config.get('azure-storage','storage_connection_string')
img_storage_container=config.get('azure-storage','container')
img_file_name_fixed = 'plant_monitor_current.jpg'
log_file_sas_url=config.get('azure-storage','log_file_sas_url')
pbi_endpoint=config.get('powerbi_streaming','streaming_endpoint')

# ---------------------------------
# Set structure for IoT message
# ---------------------------------

openweather_url = '{0}?q={1}&appid={2}&units={3}'.format(openweather_endpoint,openweather_location,openweather_api_key,openweather_units)
append_file_header = 'capturedate,weather_type,weather_description,outside_temp,outside_feels_like,outside_pressure,outside_humidity,wind_speed,wind_direction,cloud_coverage,inside_temp,inside_humidity,inside_pressure,soil_moisture\r'

# ------------------------------------
# Function to create the append blob & session
# ------------------------------------
def create_today_append_blob ():
    session_uuid = uuid.uuid4()
    today_string = now.strftime("%Y-%m-%d")
    blob_name = 'sensor-data-{0}-{1}.csv'.format(today_string,session_uuid)
    try:
        blob_client = BlobClient.from_blob_url(log_file_sas_url.format(today_string,blob_name))
        blob_exists = blob_client.exists()
        if not blob_exists:
            blob_client.create_append_blob(content_settings=ContentSettings(content_type='application/csv'), metadata=None)
        blob_client.append_block(append_file_header)
        return blob_client
    except Exception as e:
        print('Error in create_today_append_blob function:',e)


# ------------------------------------
# Function to write to the append blob
# ------------------------------------
def write_to_blob (csv_text):
    try:
        blob_client.append_block(csv_text)
    except Exception as e:
        print('Error in write_to_blob function:',e)

# ------------------------------------
# Function to write to the PBI streaming dataset
# ------------------------------------
def write_to_streaming(json_text):
    try:
        response = requests.post(pbi_endpoint,data=json_text,timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print('Error in write_to_streaming function, HTTP Error:',errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error in write_to_streaming function, Connection Error::",errc)
    except requests.exceptions.Timeout as errt:
        print ("Error in write_to_streaming function, Timeout Error::",errt)
    except requests.exceptions.RequestException as err:
        print ("Error in write_to_streaming function, Exception Error:",err)   
        

# ------------------------------------
# Create a new CSV append log for this session
# ------------------------------------
blob_client = create_today_append_blob ()

# ---------------------------------
# Initiate API and IoT and sensor sessions
# ---------------------------------
# THP sensor
thp_sensor = EasyTHPSensor()
# Azure Blob service client for images
blob_service_client = BlobServiceClient.from_connection_string(img_storage_connection_string)

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
        ow_response = requests.get(openweather_url)
        ow_json = ow_response.json()

        # -----------------------------------
        # every new day, create a new append blob file
        # -----------------------------------
        if today_string != now.strftime("%Y-%m-%d"):
            print('Creating new append log file:',now.strftime("%Y-%m-%d"))
            blob_client = create_today_append_blob()
        today_string = now.strftime("%Y-%m-%d")
        capture_date = now.strftime("%Y-%m-%d %H:%M:%S")
        # -----------------------------------
        # Build the CSV to log in Azure storage append blob
        # -----------------------------------
        csv_data = [
        now.strftime('%Y-%m-%d %H:%M:%S'), 
        ow_json['weather'][0]['main'],
        ow_json['weather'][0]['description'],
        ow_json['main']['temp'],
        ow_json['main']['feels_like'],
        ow_json['main']['pressure'],
        ow_json['main']['humidity'],
        ow_json['wind']['speed'],
        ow_json['wind']['deg'],
        ow_json['clouds']['all'],
        inside_temp,
        inside_humidity,
        inside_pressure,
        soil_moisture
        ]
        # create CSV string from the list
        csv_string = ','.join(map(str, csv_data))  +'\r'
        # append the CSV string to the log file
        write_to_blob (csv_string)

        # -------------------------------------------
        # Post the data to the Power BI Streaming dataset
        # -------------------------------------------
        pbi_data = [{
            'capturedate':now.strftime('%Y-%m-%d %H:%M:%S'),
            'outside_temp':ow_json['main']['temp'],
            'outside_feels_like':ow_json['main']['feels_like'],
            'outside_humidity':ow_json['main']['humidity'],
            'inside_temp':inside_temp,
            'inside_humidity':inside_humidity,
            'soil_moisture':soil_moisture,
            }]

        write_to_streaming(json.dumps(pbi_data))

        # -----------------------------------
        # Capture the image & save to Azure blob
        # -----------------------------------
        img_file_name_timestamp = 'image_{0}.jpg'.format(now.strftime('%Y%m%d_%H%M%S'))

        capture_diff = now - capture_date
        # only once per day, checking from mid-day
        if now.hour > 12 and capture_diff.days > 0:
            camera = picamera.PiCamera()
            camera.resolution = (640,480)
            # allow the camera to warm up & focus
            time.sleep(2)
            camera.capture(img_file_name_fixed)
            camera.close()
            capture_date = datetime.datetime.now()

            # overwrite the image used for power BI reports
            fixed_blob_client = blob_service_client.get_blob_client(container=img_storage_container,blob=img_file_name_fixed)
            with open(img_file_name_fixed,'rb') as fixxy:
                fixed_blob_client.upload_blob(fixxy,overwrite=True)

            # create timestamped version, for potential time-lapse views 
            timestamp_blob_client = blob_service_client.get_blob_client(container=img_storage_container,blob=img_file_name_timestamp)
            with open(img_file_name_fixed,'rb') as stampy:
                timestamp_blob_client.upload_blob(stampy,overwrite=True)

        print('mesage sent...',now.strftime('%Y-%m-%d %H:%M:%S'))
        time.sleep(900)

    except KeyboardInterrupt:
        print('Keyboard Interrupt accepted. The session has ended.')
        break
    except IOError as io_error:
        print('IOError:',io_error)
    except Exception as e:
        print('General Exception:', e)


