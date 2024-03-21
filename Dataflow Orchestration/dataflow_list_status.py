import azure.functions as func
import logging
import json
import datalineo as dl

def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Python HTTP trigger dataflow_list_refresh initiated')

    request_body = req.get_body()

    if not request_body:
        http_return_message = json.dumps({'status':'error', 'error_message':'api requires body for processing dataflows in json format'})
        logging.info(http_return_message)
        return func.HttpResponse(
             http_return_message,
             status_code=500
        )

    logging.info('Converting body to str & python dict')
    refresh_list_str = str(request_body, 'utf-8')
    refresh_list = json.loads(refresh_list_str)

    if not refresh_list['dataflows']:
        http_return_message = json.dumps({'status':'error', 'error_message':'api body requires \'dataflows\' key with list of datasets to be refreshed'})
        logging.info(http_return_message)
        return func.HttpResponse(
             http_return_message,
             status_code=500
        )

    logging.info('Getting access token')
    access_token = dl.get_token()

    response_list = []    
    item_count = len(refresh_list['dataflows'])
    finished_count = 0
    success_message = 'success'

    print('type refresh_list:',type(refresh_list))
    
    logging.info('Starting loop to get all dataflows status')
    for y in refresh_list['dataflows']:
        print('current loop',y)
        dataflow_workspace_guid = y['workspace']
        dataflow_guid = y['dataflow']
        dataflow_transactions = dl.dataflow_get_transactions(dataflow_workspace_guid,dataflow_guid,access_token)

        if dataflow_transactions['status'] == 'error':
            http_return_message = json.dumps({'status':'error', 'error_message':dataflow_transactions})
            logging.info(http_return_message)
            return func.HttpResponse(
                http_return_message,
                status_code=500
                )
        
        refresh_status = dataflow_transactions['current_status']

        if refresh_status == 'Failed':
            success_message = 'error'

        if refresh_status != 'InProgress':
            finished_count += 1
        
        response_list.append({'workspace':dataflow_workspace_guid, 'dataflow':dataflow_guid, 'dataflow_status':refresh_status})

    list_status = 'In Progress'
    if finished_count == item_count:
        list_status = 'Idle'
    
    http_return_message = json.dumps({'status':success_message, 'list_status':list_status, 'list_status_detail':response_list})
    return func.HttpResponse(
            http_return_message,
            status_code=200
    )

