import azure.functions as func
import logging
import json
import datalineo as dl

def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Python HTTP trigger dataflow_list_status initiated')
    
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
    
    refresh_list_x = {"dataflows":

    logging.info('Getting access token')
    access_token = dl.get_token()
    
    response_list = []
    
    for x in refresh_list['dataflows']:
        dataflow_name = x['name']
        dataflow_workspace_guid = x['workspace']
        dataflow_guid = x['dataflow']
        logging.info(f'starting process of dataset: {dataflow_name}')

        function_response = dl.dataflow_refresh(dataflow_workspace_guid, dataflow_guid, access_token)

        if function_response['status'] == 'error':
            http_return_message = json.dumps({'status':'error', 'error_message':function_response})
            logging.info(http_return_message)
            return func.HttpResponse(
                http_return_message,
                status_code=500
                )

        response_list.append(x)

    http_return_message = json.dumps({'status':'success', 'results':response_list})
    return func.HttpResponse(
            http_return_message,
            status_code=200
    )

