import json
import os
import time
from urllib import response
from xml.dom.minidom import Document
import boto3
import re
import cfnresponse

from policy_sentry.querying.actions import get_actions_with_access_level

def lambda_handler(event, context):
    try:
        response_message = main_function(event, context)
        responseData = {}
        print("Execution Successful, sending Success to CFN")
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        return {
            'statusCode': 200,
            'body': json.dumps(response_message)
        }
        
    except Exception as e: 
        print(e)
        print("Execution Failed, sending Failed to CFN")
        responseData = {"error":e}
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
        return {
            'statusCode': 500,
            'body': json.dumps("Execution failed, see Lambda logs for more details")
        }


def main_function(event, context):
    iam = boto3.resource('iam')
    ssm = boto3.client('ssm')
    
    ### INPUTS:

    brpg_access_level=os.environ['ACCESS_LEVEL']
    # brpg_access_level = ssm.get_parameters(
    #     Names=[
    #         'brpg_access_level_test',
    #     ],
    #     WithDecryption=True
    # )["Parameters"][0]["Value"]
    brpg_team_name=os.environ['TEAM_NAME']
    # brpg_team_name = ssm.get_parameters(
    #     Names=[
    #         'brpg_team_name_test',
    #     ],
    #     WithDecryption=True
    # )["Parameters"][0]["Value"]
    brpg_action_category=os.environ['ACTION_CATEGORY']
    brpg_role_or_policy=os.environ['ROLE_OR_POLICY']
    brpg_service_principal= "iam.amazonaws.com"
    brpg_role_max_session_duration = 43200
    
    timestamp = str(int(time.time()))

    brpg_role_name="BRPG_{}_{}_{}_Role_{}".format(brpg_team_name,brpg_access_level,brpg_action_category, timestamp)
    brpg_policy_name="BRPG_{}_{}_{}_Policy_{}".format(brpg_team_name,brpg_access_level,brpg_action_category,timestamp)
    brpg_description= "{} to all {} team's {} resources".format(brpg_access_level,brpg_action_category,brpg_team_name)

    print("The BRGPG Lambda will create {} and {}".format(brpg_role_name,brpg_policy_name))

    #constants
    TEAM_SERVICES = {
        "DevOps": ["eks","s3","ec2"],
        "IAM": ["iam"]
    }
    
    file = open("lambda_function/action_category_config.json")
    action_config_data = json.load(file)
    print(str(action_config_data))
    new_action_config_data = {}
    for category in action_config_data:
        new_action_config_data[category]=action_config_data[category].split(", ")

    ### slimActions is a list of slimmed version of all the read-level actions in AWS
    ### slimmed in this context means carefully used * instead of several individual actions
    unprocessedActions = []
    for service in new_action_config_data[brpg_action_category]:
        try:
            for unprocessedAction in get_actions_with_access_level(service, brpg_access_level):
                unprocessedActions.append(unprocessedAction)
        except Exception as e:
            print("While processing {}, the following warning was raised: \n{}".format(service,e))
    while("" in unprocessedActions) :
        unprocessedActions.remove("")
    
    slimActionsWithDups = []
    #Example: action = "waf:GetGeoMatchSet"
    for action in unprocessedActions:
        #Example: service = "waf:"
        service = re.findall('[a-z0-9]*:', action)[0]
        #Example: actionlist = ['Get', 'Geo', 'Match', 'Set']
        actionlist= (re.findall('[A-Z][^A-Z]*', action))
        if service != ":" and actionlist != []:
            #Example: actionitem = waf:Get*
            actionitem = service + re.findall('[A-Z][^A-Z]*', action)[0] + "*"
            slimActionsWithDups.append(actionitem)
    
    slimActions = []
    for i in slimActionsWithDups:
        if i not in slimActions:
            slimActions.append(i)
    
    #slimActions1=slimActions[0:int(len(slimActions)/2)]
    #slimActions2=slimActions[int(len(slimActions)/2):]

    # Create a policy
    brpg_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": slimActions,
                "Resource": "*",
                "Condition": {"ForAllValues:StringEquals": {"aws:ResourceTag/SupportTeam": brpg_team_name}}
            }
        ]
    }

    BRPGPolicy = iam.create_policy(
        PolicyName=brpg_policy_name,
        PolicyDocument = json.dumps(brpg_policy_document),
        Description = brpg_description,
    )
    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": brpg_service_principal
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    response_message = '''The following resources have been made:
    Policy: {}  /  {} 
    '''.format(brpg_policy_name,BRPGPolicy.arn)

    if brpg_role_or_policy == "Role":
        BRPGRole = iam.create_role(
            RoleName=brpg_role_name, 
            AssumeRolePolicyDocument = json.dumps(assume_role_policy_document),
            Description=brpg_description, 
            MaxSessionDuration=brpg_role_max_session_duration,
            #PermissionsBoundary=json.dumps(brpg_policy_document) 
        )

        BRPGRole.attach_policy(PolicyArn=BRPGPolicy.arn)

        response_message = '''The following resources have been made:
            Role: {}  /  {}
            Policy: {}  /  {} 
            '''.format(brpg_role_name,BRPGRole.arn,brpg_policy_name,BRPGPolicy.arn)
    
    print(response_message)

    return response_message
