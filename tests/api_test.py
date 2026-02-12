import urllib.request
import json
import os

# Request data goes here
# The example below assumes JSON formatting which may be updated
# depending on the format your endpoint expects.
# More information can be found here:
# https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script
data = {
    "age": 25,
    "scholarship": 1,
    "hipertension": 0,
    "diabetes": 0,
    "alcoholism": 0,
    "handcap": 0,
    "sms_received": 0,
    "lead_time_days": 21,
    "day_of_week": 4,
    "chronic_conditions": 0
}

body = str.encode(json.dumps(data))

url = 'https://noshow-online-endpoint.swedencentral.inference.ml.azure.com/score'
# Get API key from environment variable (do not hardcode!)
# Set via: export AZURE_ML_API_KEY="your-key" or use Azure CLI:
# az ml online-endpoint get-credentials --name noshow-online-endpoint -g rg-ai-hub-citadel-dev-02 -w AI-WORKSPACE-shark
api_key = os.environ.get('AZURE_ML_API_KEY', '')
if not api_key:
    raise Exception("Set AZURE_ML_API_KEY environment variable")


headers = {'Content-Type':'application/json', 'Accept': 'application/json', 'Authorization':('Bearer '+ api_key)}

req = urllib.request.Request(url, body, headers)

try:
    response = urllib.request.urlopen(req)

    result = response.read()
    print(result)
except urllib.error.HTTPError as error:
    print("The request failed with status code: " + str(error.code))

    # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
    print(error.info())
    print(error.read().decode("utf8", 'ignore'))