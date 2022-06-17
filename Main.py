import os
import json
import requests
import boto3

"""
Overview: SumoLogic is used to collect log data from a fleet of endpoints. 
SumoLogic collectors are installed, but are considered ephemeral. 
Dead collectors need to be identified and deleted from the Sumo account using their API. 

Requirements: API documentation contained at: https://help.sumologic.com/APIs/Collector-Management-API/Collector-API-Methods-and-Examples 

1. List offline collectors that have been offline for more than 14 days "use alivebeforedays" argument 
2. For collectors that meet this criteria, delete the corresponding collector(s) using the delete collector by ID method. 
3. Send list of collectors that have been deleted to an email address (to be provided). Email should contain the collector info (Get Collector by ID) 
4. Code should run as a Lambda function every 24 hours 
"""

username = os.getenv("ACCESS_ID")
password = os.getenv("ACCESS_KEY")
auth = (username, password)

def delete_collector(collector_id):
    res = requests.get(f"https://api.sumologic.com/api/v1/collectors/{collector_id}", auth=auth)
    data = res.json()
    res = requests.delete(f"https://api.sumologic.com/api/v1/collectors/{collector_id}", auth=auth)
    return data

def send_sns_email(email_body):
    
    client = boto3.client('sns', region_name='us-west-2')

    snsArn = os.getenv("SNS_ARN")

    response = client.publish(
        TargetArn = snsArn,
        Message = email_body,
        Subject='Deleted Collectors from SumoLogic'
    )
    
def lambda_handler(event, context):
    params = {
        "aliveBeforeDays": 14
    }
    res = requests.get("https://api.sumologic.com/api/v1/collectors/offline", auth=auth, params=params)

    dead_ids = [str(c['id']) for c in res.json()["collectors"]]

    collectors_info = []
    for collector_id in dead_ids:
        collectors_info.append(
           delete_collector(collector_id)
        )
    
    if dead_ids:
        email_body = f"""
        The following collectors have been deleted:
            {dead_ids}   
        
        {json.dumps(collectors_info, indent=4)}
        """

    else:
        email_body = "No dead collectors have been deleted"

    send_sns_email(email_body)
