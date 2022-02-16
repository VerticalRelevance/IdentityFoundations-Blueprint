from aws_cdk import (
    aws_iam as iam,
    core
)

import re
import json

from policy_sentry.querying.actions import get_actions_with_access_level


class BRPGStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### INPUTS:
        brpg_team_name="DevOps"
        #options for access level include 'Read', 'Write', 'List', 'Permisssions management', or 'Tagging'
        brpg_access_level="Write"
        brpg_service_principal= "iam.amazonaws.com"
        brpg_role_max_session_duration = 43200

        brpg_role_name="BRPG_{}_{}_Role".format(brpg_team_name,brpg_access_level)
        brpg_policy_name="BRPG_{}_{}_Policy".format(brpg_team_name,brpg_access_level)
        brpg_description= "{} to all {} resources".format(brpg_access_level, brpg_team_name)
        
        #constants
        TEAM_SERVICES = {
            "DevOps": ["eks","s3","ec2"],
            "IAM": ["iam"]
        }

        ### slimActions is a list of slimmed version of all the read-level actions in AWS
        ### slimmed in this context means carefully used * instead of several individual actions
        unprocessedActions = []
        for service in TEAM_SERVICES[brpg_team_name]:
            for unprocessedAction in get_actions_with_access_level(service, brpg_access_level):
                unprocessedActions.append(unprocessedAction)
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

        BRPGPolicy = iam.ManagedPolicy(
            self, brpg_policy_name,
            description=brpg_description,
            managed_policy_name=brpg_policy_name,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= slimActions,
                    resources=["*"],
                    conditions={"ForAllValues:StringEquals": {"aws:ResourceTag/SupportTeam": brpg_team_name}}
                )
            ]
        )

        iam.Role(
            self, brpg_role_name, 
            assumed_by=iam.ServicePrincipal(brpg_service_principal),
            description=brpg_description, 
            #external_id=None, 
            #external_ids=None, 
            #inline_policies=None, 
            managed_policies=[BRPGPolicy],
            max_session_duration=core.Duration.seconds(brpg_role_max_session_duration),
            path=None,
            permissions_boundary=BRPGPolicy, 
            role_name=brpg_role_name
        )