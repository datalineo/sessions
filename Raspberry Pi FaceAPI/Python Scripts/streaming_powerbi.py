import grovepi
import time
import json
import http.client, urllib.request, urllib.parse, urllib.error
from configparser import SafeConfigParser

http_endpoint = 'api.powerbi.com'
headers = {'Content-Type': "application/json",}

config_file = r'/home/pi/config_faceapi.ini'
config=SafeConfigParser()
config.read(config_file)
pbi_key = config.get('streaming_powerbi','key')
pbi_beta = config.get('streaming_powerbi','beta')
pbi_dataset = config.get('streaming_powerbi','dataset')
http_folder = '/beta/'+pbi_beta+'/datasets/'+pbi_dataset+'/rows?key='+pbi_key

ultrasonic_ranger = 2 # digital port D2
sound_sensor = 0 # analog port A0
light_sensor = 1 #analog port A1

grovepi.pinMode(sound_sensor,"INPUT")
grovepi.pinMode(light_sensor,"INPUT")

print("Kicking off stream")

while True:
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        # Read the sound level
        value_sound = grovepi.analogRead(sound_sensor)
        value_range = grovepi.ultrasonicRead(ultrasonic_ranger)
        value_light = grovepi.analogRead(light_sensor)

        payload = {
        "sensordate":now,
        "sound":value_sound,
        "range":value_range,
        "light":value_light
        }

        payload_json = '['+json.dumps(payload)+']'
        
        #print(payload_json)
        try:
            conn = http.client.HTTPSConnection(http_endpoint)
            conn.request("POST", http_folder, payload_json, headers)
            response = conn.getresponse()
            data = response.read()
            print('http response:',data)
            conn.close()
        except Exception as e:
            print("[Errno {0}]".format(e))

        #print("value_sound = %d" %value_sound, "value_range = %d" %value_range, "value_light = %d" %value_light)

        time.sleep(0.5)

    except IOError:
        print ("Error")
    except KeyboardInterrupt:
        print("Goodbye")
        break
