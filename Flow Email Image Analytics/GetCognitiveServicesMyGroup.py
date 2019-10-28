import http.client, urllib.request, urllib.parse, urllib.error
import json
import configparser

person_group_id = 'mygroup'
config_file = r'C:\GIT\config\config_faceapi.ini'
config=configparser.ConfigParser()
config.read(config_file)
cognitive_services_key = config.get('faceapi','cognitive_services_key')
cognitive_services_endpoint = config.get('faceapi','cognitive_services_endpoint')

# - lists the details of one group in the subscription
def group_get(person_group_id):
    headers = {
        'Ocp-Apim-Subscription-Key': cognitive_services_key,
        }
    try:
        conn = http.client.HTTPSConnection(cognitive_services_endpoint)
        conn.request("GET", "/face/v1.0/persongroups/{0}".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# gets details of one person in a group
def person_get(person_group_id, person_id):

    headers = {
        'Ocp-Apim-Subscription-Key': cognitive_services_key,
        }
    try:
        conn = http.client.HTTPSConnection(cognitive_services_endpoint)
        conn.request("GET", "/face/v1.0/persongroups/{0}/persons/{1}".format(person_group_id,person_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        #print(data)
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))


# deletes ther person from the group
def person_delete(person_group_id, person_id):  
    headers = {
        'Ocp-Apim-Subscription-Key': cognitive_services_key,
        }
    try:
        conn = http.client.HTTPSConnection(cognitive_services_endpoint)
        conn.request("DELETE", "/face/v1.0/persongroups/{0}/persons/{1}".format(person_group_id,person_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

# lists the persons in the person group
def person_group_get(person_group_id):

    headers = {
        'Ocp-Apim-Subscription-Key': cognitive_services_key,
    }

    try:
        conn = http.client.HTTPSConnection(cognitive_services_endpoint)
        conn.request("GET", "/face/v1.0/persongroups/{0}/persons".format(person_group_id), None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return(data)
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

def json_print(json_text):
    json_text = json_text.decode("utf-8")
    print(json.dumps(json.loads(json_text),indent=2))
    
#person_delete(person_group_id, "81acaf8f-c24d-49a5-b89f-7d081a3c69eb")
#person_delete(person_group_id, "37b085ff-a28d-4d45-a16f-7361276be876")

group_list = person_group_get(person_group_id)
json_print(group_list)

