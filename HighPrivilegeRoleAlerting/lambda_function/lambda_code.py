import json
import os
import time
import boto3

import pytz
from datetime import datetime, timezone
from tzlocal import get_localzone

def lambda_handler(event, context):
    sns_client = boto3.client('sns')
    topic_arn = os.environ["TOPICARN"]
    role_name = os.environ["ROLE_NAME"]

    utc_dt = datetime.now(timezone.utc)
    
    EST = pytz.timezone('US/Eastern')
    PST = pytz.timezone('US/Pacific')
    esttime = utc_dt.astimezone(EST).isoformat()
    psttime = utc_dt.astimezone(PST).isoformat()
    
    # Use astimezone() without an argument
    # print("Local time   {}".format(utc_dt.astimezone().isoformat()))
    
    # Use tzlocal get_localzone
    # print("Local time   {}".format(utc_dt.astimezone(get_localzone()).isoformat()))
    
    # Explicitly create a pytz timezone object
    # Substitute a pytz.timezone object for your timezone
    # print("Local time   {}".format(utc_dt.astimezone(NZST).isoformat()))
    
    message = "The role '{}' was logged into at {}(EST) / {}(PST)".format(role_name,esttime,psttime)
    print(message)
    print("Sending message to SNS topic: {}".format(topic_arn))
    response = sns_client.publish(
        TopicArn=topic_arn,
        # TargetArn='string',
        # PhoneNumber='string',
        Message=message,
        Subject='High-Privilege Role Alerting',
        # MessageStructure='string',
        # MessageAttributes={
        #     'string': {
        #         'DataType': 'string',
        #         'StringValue': 'string',
        #         'BinaryValue': b'bytes'
        #     }
        # },
        # MessageDeduplicationId='string',
        # MessageGroupId='string'
    )
    
    response_message = message
    return {
        'statusCode': 200,
        'body': json.dumps(response_message)
    }