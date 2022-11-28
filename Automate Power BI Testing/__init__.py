import logging
import os
import pandas as pd
import azure.functions as func
import datetime
import json
import sqlalchemy
import datalineo as dl
import uuid
from azure.storage.blob import BlobClient
from azure.identity import ClientSecretCredential, DefaultAzureCredential
import requests


# -----------------------------------------------
# function to take a data frame and standardize the structure for comparisons
# -----------------------------------------------

def standardize_dataframe(df, date_column_list):
        # Set all column headers to 1,2,3..
        # set any date/time columns to the correct data type
        df.columns = range(df.shape[1])
        df[date_column_list] = df[date_column_list].apply(pd.to_datetime)
        return df

# -----------------------------------------------
# Execute the DAX query, via Power BI REST API
# -----------------------------------------------

def execute_dax_query(dataset_id, dax_query, access_token):

    header = {
        'Content-Type':'application/json',
        'Authorization': f'Bearer {access_token}'
        }

    body = {
        'queries': [
            {'query': dax_query}
        ],
        'serializerSettings': {'incudeNulls': 'true'}
        }

    activityevents_uri = f'https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries'

    response = requests.post(activityevents_uri, headers=header, data=json.dumps(body))

    # need to convert response to utf-8-sig as Azure Functionon Linux handles this differently to script run from Windows OS
    response.encoding='utf-8-sig'

    if response.status_code != 200:    
        return {
            'error':'api error',
            'status_code':response.status_code,
            'response_reason':response.text
        }
    else:
        return {
            'result_set':response.json()['results'][0]['tables'][0]['rows']
        }

# -----------------------------------------------
# Authenticate function
# -----------------------------------------------

def get_token():
    client_credential_class = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    access_token_class = client_credential_class.get_token(powerbi_api_scope)
    return access_token_class.token
	

# -----------------------------------------------
# Main function, where we do all of the work!
# -----------------------------------------------

def main(req: func.HttpRequest) -> func.HttpResponse:
        logging.info('Python HTTP trigger function processed a request.')

        current_time = datetime.datetime.now().isoformat()
        sql_tests_query = 'select [TestId], [QuerySql], [QueryDax], [DateColumnList] from [av].[ValidationTests]'
        execution_id = uuid.uuid4()
    
        try:
                # Grab environment variables
                # Dataset could be moved to an Api parameter to allow more flexibility
                # create an empty list for the result set
                dataset_id = os.environ['dlPowerBiDataset']
                av_conn_string = os.environ['dlAvConnString']
                source_conn_string = os.environ['dlSourceConnString']
                blob_container = os.environ['dlBlobContainer']
                blob_sas_token = os.environ['dlBlobSasToken']
                results_list = []

                # Create connections to AutoValidation SQL database and source (to text against) SQL database
                av_engine = sqlalchemy.create_engine(av_conn_string,echo=False)
                source_engine = sqlalchemy.create_engine(source_conn_string,echo=False)
            
                # Get the list of SQL & DAX queries and convert to a list
                test_data = pd.read_sql(sql_tests_query, av_engine)
                test_list = json.loads(test_data.to_json(orient='records'))

                # Authenticate for Power BI Rest API exection
                access_token = dl.get_token()

                for x in test_list:
                        test_id = x['TestId']
                        query_sql = x['QuerySql']
                        query_dax = x['QueryDax']
                        date_column_list = []
                        if x['DateColumnList']: date_column_list = json.loads(x['DateColumnList'])
                        
                        # --------------------------------------
                        #  Get the SQL result set and standardize the shape
                        # --------------------------------------
                        df_sql = pd.read_sql_query(sql=query_sql, con=source_engine)
                        standardize_dataframe(df_sql,date_column_list)
                        
                        # --------------------------------------
                        #  Call the API to run the DAX query, error handling
                        # --------------------------------------
                        dax_response = execute_dax_query(dataset_id=dataset_id, dax_query=query_dax, access_token=access_token)

                        if 'error' in dax_response: 
                                response_reason = dax_response['response_reason']
                                status_code = dax_response['status_code']
                                error_text = json.dumps({'result':'error', 'error_message':f'status_code:{status_code}, response_reason:{response_reason}'})
                                logging.info(f'Datalineo: error in dax_result: {error_text}')
                                return func.HttpResponse(
                                        error_text,
                                        status_code=status_code
                                        )
                        else:
                                dax_dataset = dax_response['result_set']

                        # --------------------------------------
                        # Get the DAX query results into a dataframe & standardize the shape
                        # --------------------------------------
                        df_dax = pd.read_json(path_or_buf=json.dumps(dax_dataset), convert_dates=True, precise_float=True)
                        standardize_dataframe(df_dax,date_column_list)
                        
                        # --------------------------------------
                        # Perform the comparison
                        # --------------------------------------
                        df_compare = df_sql.compare(df_dax, align_axis=0)
                        
                        # temp code to write the comparison results to a file
                        blob_url = None
                        if df_compare.empty:
                                test_result = 0
                        else:
                                test_result = 1
                                blob_url = f'{blob_container}/{execution_id}-{test_id}.csv'
                                blob_client = BlobClient.from_blob_url(f'{blob_url}{blob_sas_token}')
                                blob_data = df_compare.to_csv()
                                blob_client.upload_blob(blob_data,overwrite=True)
                                #df_sql.to_csv(r'C:\temp\AutoValidation\df_sql_{0}.csv'.format(test_id))
                                #df_dax.to_csv(r'C:\temp\AutoValidation\df_dax_{0}.csv'.format(test_id))
                                #df_compare.to_csv(r'C:\temp\AutoValidation\compare_{0}.csv'.format(test_id))

                        # --------------------------------------
                        #  Compare the hash's and create the tuple for this loop's result & append 
                        # --------------------------------------
                        results_list.append({'ExecutionId':execution_id,'TestId':test_id, 'TestResult':test_result, 'CreatedDate':current_time, 'TestFailureFileURL':blob_url})
                
                # --------------------------------------
                # With the completed results in results_list objects, write to SQL
                # in the ValidationTestResults table
                # --------------------------------------
                
                df_output = pd.DataFrame.from_dict(results_list)
                insert_result = df_output.to_sql(name='ValidationTestResults', con=av_engine, schema='av', if_exists='append', index=False, method='multi')
                
                if insert_result > 0: 
                        response_message = json.dumps({'result':'success', 'message':f'{insert_result} tests completed'})
                else:
                        response_message = json.dumps({'result':'error', 'error_message':'Command successful but zero rows inserted'})
                        return func.HttpResponse(
                                response_message,
                                status_code=500
                        )

                #response_message = json.dumps({'result':'success', 'message':f'{insert_result} tests completed'})

        # Exception block, in case of any SQL/ODBC errors, catch & return        
        except sqlalchemy.exc.SQLAlchemyError as e:
                response_message = json.dumps({'error':str(e)})
                return func.HttpResponse(
                        response_message,
                        status_code=500
                )

        # Everything completed successfully
        return func.HttpResponse(
                response_message,
                status_code=200
        )