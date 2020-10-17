# ---------------------------------
# This script reads the moisture value from a Raspberry Pi Sensor, add current weather 
# conditions and sends to Azure IoT Hub
# ---------------------------------

import time
import grovepi
import requests
from configparser import ConfigParser
from azure.iot.device import IoTHubDeviceClient, Message
import json
import datetime

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
# Set variables
# ---------------------------------

iot_text = '{{"moisture": {moisture},"weather":{humidity}}}'
sensor = 0
url = '{0}?q={1}&appid={2}&units={3}'.format(endpoint,location,api_key,units)


# ---------------------------------
# Initiate API and IoT sessions
# ---------------------------------
session = requests.session()
iot_client = IoTHubDeviceClient.create_from_connection_string(iot_connection_string)


while True:
    try:
        now = datetime.datetime.now()
        moisture = grovepi.analogRead(sensor)
        response = session.get(url)
        iot_message_json = response.json()
        iot_message_json['moisture']=moisture
        iot_message_json['capturedate']=now.strftime('%Y-%m-%d %H:%M:%S')
        iot_message = Message(json.dumps(iot_message_json))
        iot_client.send_message(iot_message)
        print('mesage sent...',now.strftime('%Y-%m-%d %H:%M:%S'))
        time.sleep(120)

    except KeyboardInterrupt:
        print ('Session ended by user')
        break
    except IOError:
        print ("Error")
