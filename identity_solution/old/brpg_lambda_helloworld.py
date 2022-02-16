import json
import os

def lambda_handler(event, context):
    access_level = os.environ['ACCESS_LEVEL']
    team_name = os.environ['TEAM_NAME']

    return {
        'statusCode': 200,
        'body': json.dumps("So you need access to the '{}' team's resources at a '{}' access level?".format(access_level,team_name))
    }
