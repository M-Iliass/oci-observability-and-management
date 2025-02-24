import os
import io
import json
import logging
import oci
import datetime

from fdk import response
from urllib.parse import urlparse
from urllib.parse import parse_qs
from urllib.parse import unquote

def handler(ctx, data: io.BytesIO = None):

    parsed_url = urlparse(ctx.RequestURL())
    query_params = parse_qs(parsed_url.query)

    if "query_result_name" in query_params:
        query_name = query_params['query_result_name'][0]
        query_text = "fetch query result " + query_name
    elif "query_tql" in query_params:
        query_text = unquote(query_params['query_tql'][0])
    elif "configuration_name" in query_params:
        configuration_name = query_params['configuration_name'][0]
        if configuration_name in os.environ:
            query_text = os.environ[configuration_name]
        else:
            logging.getLogger().error("Configuration param doesn't exist: " + configuration_name)
            return response.Response(ctx, status_code=400, response_data="Incorrect configuration name")
    else:
        logging.getLogger().error("No valid parameters specified, you need to specify one of the following paramaters:\nquery_result_name, query_tql, configuration_name")
        return response.Response(ctx, status_code=400, response_data="No valid parameters specified")

    apm_domain_id = os.environ['apm_domain_id']

    apm_traces_client = get_traces_client()

    query_response = apm_traces_client.query(apm_domain_id=apm_domain_id,
                                            query_details=oci.apm_traces.models.QueryDetails(query_text=query_text),
                                            time_span_started_greater_than_or_equal_to=datetime.datetime.fromtimestamp(0),
                                            time_span_started_less_than=datetime.datetime.fromtimestamp(0),
                                            limit=900)
    
    if is_timeseries_data(query_response.data):
        result = transform_time_series_data(query_response.data)
    else:
        result = transform_data(query_response.data)
    
    result = json.dumps(result, sort_keys=True, indent=2, separators=(',', ': '))

    return response.Response(
        ctx, response_data=result,
        headers={"Content-Type": "application/json"}
    )

def get_traces_client():
    # ### Use the below config to run locally using config file authentication
    # config = oci.config.from_file(profile_name="")
    # token_file = config['security_token_file']
    # token = None
    # with open(token_file, 'r') as f:
    #     token = f.read()

    # private_key = oci.signer.load_private_key_from_file(config['key_file'])
    # signer = oci.auth.signers.SecurityTokenSigner(token, private_key) 
    # apm_traces_client = oci.apm_traces.QueryClient({'region': config['region']}, signer=signer)

    signer = oci.auth.signers.get_resource_principals_signer()
    apm_traces_client = oci.apm_traces.QueryClient(config={}, signer=signer)

    return apm_traces_client


def is_timeseries_data(data):
    for column in data.query_result_metadata_summary.query_result_row_type_summaries:
        if column.expression == "timeseries":
            return True
    return False

### Transforms normal non-Timeseries data
# The basic output would be a key value representation of each trace, array columns will be simplified as well for ease of use (for the first dimension)
def transform_data(data):
    date_columns = []
    for column in data.query_result_metadata_summary.query_result_row_type_summaries:
        if column.unit == "EPOCH_TIME_MS":
            date_columns.append(column.display_name)
    
    result = []

    for row in data.query_result_rows:
        new_row = row.query_result_row_data

        for key in list(new_row.keys()):
            if hasattr(new_row[key], "__len__") and (not isinstance(new_row[key], str)):
                for i in range(len(new_row[key])):
                    new_row[key][i] = new_row[key][i]["queryResultRowData"]

        for column in date_columns:
            new_row[column] = datetime.datetime.fromtimestamp(new_row[column] / 1000.0, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        result.append(new_row)
    
    return result

### Transforms Timeseries to an easier to use, simple to read format
def transform_time_series_data(data):
    grouped_by_columns = []
    for column in data.query_result_metadata_summary.query_results_grouped_by:
        grouped_by_columns.append(column.query_results_grouped_by_column)
    for column in data.query_result_metadata_summary.query_result_row_type_summaries:
        if column.expression in grouped_by_columns:
            grouped_by_columns.remove(column.expression)
            grouped_by_columns.append(column.display_name)
    
    result = []
    for row in data.query_result_rows:
        timeseries = row.query_result_row_data['timeseries']

        for ts_row in timeseries:
            new_row = ts_row['queryResultRowData']

            for key in list(new_row.keys()):
                if key.startswith("time_bucket("):
                    bucket_in_minute = int(key.split('(')[1].split(',')[0])
                    date = datetime.datetime.fromtimestamp(new_row[key]* bucket_in_minute * 60, tz=datetime.timezone.utc)
                    new_row.pop(key, None)
                    new_row.update({"date": date.strftime('%Y-%m-%dT%H:%M:%SZ')})

            for name in grouped_by_columns:
                new_row.update({name: row.query_result_row_data[name]})
            
            result.append(new_row)
    
    return result

### Invoke this function using the code bellow, set the query name and apm_domain_id and also make sure you use the correct code at the method 'get_traces_client'
# query_name = ""
# apm_domain_id = ""

# os.environ["apm_domain_id"] = apm_domain_id
# handler(ctx = InvokeContext("app_id", "app_name", "fn_id", "fn_name", "call_id", request_url="/query?query_result_name=" + query_name))
