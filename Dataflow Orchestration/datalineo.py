
from azure.identity import ClientSecretCredential, DefaultAzureCredential
import os
import requests
import json

powerbi_api_scope = 'https://analysis.windows.net/powerbi/api/.default'
client_id = os.environ['PowerBiAppRegClientId']
client_secret = os.environ['PowerBiAppRegClientSecret']
tenant_id = os.environ['TenantId']


def get_token():
    client_credential_class = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    access_token_class = client_credential_class.get_token(powerbi_api_scope)
    return access_token_class.token

def dataflow_get_transactions(workspace_guid, dataflow_guid, access_token):

    endpoint = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_guid}/dataflows/{dataflow_guid}/transactions'

    header = {
        'Content-Type':'application/json',
        'Authorization': f'Bearer {access_token}'
        }

    response = requests.get(url=endpoint, headers=header)
    refresh_transactions = response.json()['value']
    
    if response.status_code == 200:
        current_status = refresh_transactions[0]['status']
        return {
            'status':'success',
            'refresh_transactions':refresh_transactions,
            'current_status':current_status
        }
    else:
        return {
            'status':'error',
            'status_code':response.status_code,
            'response_reason':response.text
        }

def dataflow_refresh(workspace_guid, dataflow_guid, access_token):

    endpoint = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_guid}/dataflows/{dataflow_guid}/refreshes'

    header = {
        'Content-Type':'application/json',
        'Authorization': f'Bearer {access_token}'
        }

    body = json.dumps({'notifyOption':'NoNotification'})
    response = requests.post(url=endpoint,headers=header,data=body)

    if response.status_code == 200:
        return {
            'status':'success'
        }
    else:
        return {
            'status':'error',
            'status_code':response.status_code,
            'response_reason':response.text
        }

