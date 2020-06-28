import time
import grovepi
import requests
from configparser import ConfigParser
from azure.iot.device import IoTHubDeviceClient, Message
import json
import datetime

sensor = 0
config_file = '/home/pi/GIT/config/config_moisture.ini'
config=ConfigParser()
config.read(config_file)

endpoint = config.get('openweathermap','endpoint')
api_key = config.get('openweathermap','api_key')
location = config.get('openweathermap','location')
units = config.get('openweathermap','units')
iot_connection_string = config.get('azure-iot','iot-connection-string')
iot_text = '{"moisturecc": {moisture}}'
MSG_TXT = '{{"moisture": {moisture},"weather":{humidity}}}'

url = '{0}?q={1}&appid={2}&units={3}'.format(endpoint,location,api_key,units)

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
        #print(iot_message)
        iot_client.send_message(iot_message)
        print('mesage sent...',now.strftime('%Y-%m-%d %H:%M:%S'))
        time.sleep(120)

    except KeyboardInterrupt:
        break
    except IOError:
        print ("Error")
