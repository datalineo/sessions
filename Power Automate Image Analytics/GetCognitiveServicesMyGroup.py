import json
import configparser
import requests

person_group_id = 'mygroup'
config_file = r'C:\GIT\datalineo\config\config_faceapi.ini'
config=configparser.ConfigParser()
config.read(config_file)
cognitive_services_key = config.get('faceapi','cognitive_services_key')
cognitive_services_endpoint = config.get('faceapi','cognitive_services_endpoint')

headers = {
    'Ocp-Apim-Subscription-Key': cognitive_services_key,
    }

# - lists the details of one group in the subscription
def group_get(person_group_id):
    session = requests.session()
    try:
        response = session.get(cognitive_services_endpoint+"/face/v1.0/persongroups/{0}".format(person_group_id), headers=headers)
        file_data = response.content
        return(file_data)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

# gets details of one person in a group
def person_get(person_group_id, person_id):
    session = requests.session()
    try:
        response = session.get(cognitive_services_endpoint+'/face/v1.0/persongroups/{0}/persons/{1}'.format(person_group_id,person_id), headers=headers)
        return(response.content)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

# deletes the person from the group
def person_delete(person_group_id, person_id):  
    session = requests.session()
    try:
        response = session.delete(cognitive_services_endpoint+'/face/v1.0/persongroups/{0}/persons/{1}'.format(person_group_id,person_id), headers=headers)
        return(response.content)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

# lists the persons in the person group
def person_group_get(person_group_id):
    session = requests.session()
    try:
        response = session.get(cognitive_services_endpoint+'/face/v1.0/persongroups/{0}/persons'.format(person_group_id), headers=headers)
        return(response.content)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

def json_print(json_text):
    json_text = json_text.decode('utf-8')
    print(json.dumps(json.loads(json_text),indent=2))
    
#person_delete(person_group_id, '81acaf8f-c24d-49a5-b89f-7d081a3c69eb')
#person_delete(person_group_id, "c7f09d32-6ac8-4aee-bb54-73c7c77bc0e2")

group_list = person_group_get(person_group_id)
json_print(group_list)

