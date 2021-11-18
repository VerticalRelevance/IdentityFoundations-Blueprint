from aws_cdk import (
    aws_iam as iam,
    core
)

import requests
import re

class IdentitySolutionStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        #Get List of All AWS Services' IAM Prefixes
        r =requests.get('https://awspolicygen.s3.amazonaws.com/js/policies.js')
        p = re.compile(r'StringPrefix":"(?P<prefix>[a-z0-9]*)')
        servicesListWithDups = p.findall(r.text)

        #RemoveDuplicates
        servicesList = []
        for i in servicesListWithDups:
            if i not in servicesList:
                servicesList.append(i)


        print(servicesList)

        describeServicesList = []
        listServicesList = []
        getServicesList = []

        for service in servicesList:
            describeServicesList.append(service+":Describe*")
            listServicesList.append(service+":List*")
            getServicesList.append(service+":Get*")

        FullIAMPolicy = iam.ManagedPolicy(
            self, "FullIAMPolicy",
            description="Full-Control Access to IAM resources, Read Organizations",
            managed_policy_name="FullIAMPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "iam:*",
                        "organizations:Describe*",
                        "organizations:List*"
                    ],
                    resources=["*"])
            ],
        )

        ReadIAMPolicy = iam.ManagedPolicy(
            self, "ReadIAMPolicy",
            description="Read Access to IAM resources",
            managed_policy_name="ReadIAMPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "iam:List*",
                        "iam:Get*"
                    ],
                    resources=["*"])
            ],
        )

        FullBillingPolicy = iam.ManagedPolicy(
            self, "FullBillingPolicy",
            description="Full-Control Access to Billing resources",
            managed_policy_name="FullBillingPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "aws-portal:*"
                    ],
                    resources=["*"])
            ],
        )

        ReadBillingPolicy = iam.ManagedPolicy(
            self, "ReadBillingPolicy",
            description="Read Access to Billing resources",
            managed_policy_name="ReadBillingPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "aws-portal:View*"
                    ],
                    resources=["*"])
            ],
        )

        FullAllExceptBillingPolicy = iam.ManagedPolicy(
            self, "FullExceptBilling",
            description="Full Access to all except billing",
            managed_policy_name="FullExceptBilling",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= ["*"],
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid = "DenyBilling",
                    actions= [
                        "aws-portal:*",
                        "cur:*",
                        "ce:*",
                        "pricing:*",
                        "purchase-orders:*"
                    ],
                    resources=["*"])
            ],
        )    

        DescribeAllExceptBillingPolicy = iam.ManagedPolicy(
            self, "DescribeAllExceptBilling",
            description="Describe Access to all except billing",
            managed_policy_name="DescribeExceptBilling",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= describeServicesList,
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid = "DenyBilling",
                    actions= [
                        "aws-portal:*",
                        "cur:*",
                        "ce:*",
                        "pricing:*",
                        "purchase-orders:*"
                    ],
                    resources=["*"])
            ],
        )

        ListAllExceptBillingPolicy = iam.ManagedPolicy(
            self, "ListAllExceptBilling",
            description="List Access to all except billing",
            managed_policy_name="ListAllExceptBilling",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= listServicesList,
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid = "DenyBilling",
                    actions= [
                        "aws-portal:*",
                        "cur:*",
                        "ce:*",
                        "pricing:*",
                        "purchase-orders:*"
                    ],
                    resources=["*"])
            ],
        )

        GetAllExceptBillingPolicy = iam.ManagedPolicy(
            self, "GetAllExceptBilling",
            description="Get Access to all except billing",
            managed_policy_name="GetAllExceptBilling",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= getServicesList,
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid = "DenyBilling",
                    actions= [
                        "aws-portal:*",
                        "cur:*",
                        "ce:*",
                        "pricing:*",
                        "purchase-orders:*"
                    ],
                    resources=["*"])
            ],
        ) 

        FullDevOpsTeamResourcesPolicy = iam.ManagedPolicy(
            self, "FullDevOpsTeamResourcesPolicy",
            description="Access to resources used by DevOps team",
            managed_policy_name="FullDevOpsTeamResourcesPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowDevOps",
                    actions= ["*"],
                    resources=["*"],
                    conditions={"ForAllValues:StringEquals": {"aws:ResourceTag/SupportTeam": "DevOps"}})
            ],
        )
        FullNetworkTeamResourcesPolicy = iam.ManagedPolicy(
            self, "FullNetworkTeamResourcesPolicy",
            description="Access to all actions for network team's resources",
            managed_policy_name="FullNetworkTeamResourcesPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowAllActionsForNetworkResources",
                    actions= ["*"],
                    resources=["*"],
                    conditions={"ForAllValues:StringEquals": {"aws:ResourceTag/SupportTeam": "Network"}}),
            ],
        )

        FullNetworkActionsPolicy = iam.ManagedPolicy(
            self, "FullNetworkActionsPolicy",
            description="Access to all network actions on all resources",
            managed_policy_name="FullNetworkActionsPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowAllNetworkActions",
                    actions= [
                        "ec2:*Network*",
                        "ec2:*Address*",
                        "ec2:*Dhcp*",
                        "ec2:*Vpc*",
                        "ec2:*Vpn*",
                        "ec2:*Route*",
                        "ec2:*SecurityGroup*",
                        "ec2:*Subnet*",
                        "ec2:*Gateway*",
                    ],
                    resources=["*"])
            ],
        )

        ReadNetworkActionsPolicy = iam.ManagedPolicy(
            self, "ReadNetworkActionsPolicy",
            description="Read access to all network resources",
            managed_policy_name="ReadNetworkActionsPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowAllReadNetworkActions",
                    actions= [
                        "ec2:Describe*Network*",
                        "ec2:Describe*Address*",
                        "ec2:Describe*Dhcp*",
                        "ec2:Describe*Vpc*",
                        "ec2:Describe*Vpn*",
                        "ec2:Describe*Route*",
                        "ec2:Describe*SecurityGroup*",
                        "ec2:Describe*Subnet*",
                        "ec2:Describe*Gateway*",
                    ],
                    resources=["*"])
            ],
        )

        FullOrganizationsPolicy = iam.ManagedPolicy(
            self, "FullOrganizationsPolicy",
            description="Access to all Organizations actions",
            managed_policy_name="FullOrganizationsPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowAllOrganizatrionsActions",
                    actions= [
                        "organizations:*"
                    ],
                    resources=["*"])
            ],
        )

        FullAccountPolicy = iam.ManagedPolicy(
            self, "FullAccountPolicy",
            description="Access to all account actions",
            managed_policy_name="FullAccountPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "AllowFullAccount",
                    actions= [
                        "account:*"
                    ],
                    resources=["*"])
            ],
        )

        ReadOrganizationsPolicy = iam.ManagedPolicy(
            self, "ReadOrganizationsPolicy",
            description="Read access to all Organizations actions",
            managed_policy_name="ReadOrganizationsPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "ReadOrganizations",
                    actions= [
                        "organizations:Describe*",
                        "organizations:List*",
                        "organizations:Get*"
                    ],
                    resources=["*"])
            ],
        )

        ReadAccountPolicy = iam.ManagedPolicy(
            self, "ReadAccountPolicy",
            description="Read access to all account actions",
            managed_policy_name="ReadAccountPolicy",
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    sid = "ReadAccount",
                    actions= [
                        "account:Describe*",
                        "account:List*",
                        "account:Get*"
                    ],
                    resources=["*"])
            ],
        )

        roledict = [
            {
                "name": "AccessAdministrator",
                "policies": [FullIAMPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "AccessAuditor",
                "policies": [ReadIAMPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "BillingAdministrator",
                "policies": [FullBillingPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "BillingAuditor",
                "policies": [ReadBillingPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "Break-Glass",
                "policies": [FullAllExceptBillingPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "CloudAdministrator",
                "policies": [FullAllExceptBillingPolicy],
                "permissions_boundary": FullAllExceptBillingPolicy,
            },
            {
                "name": "LOBx-DevOpsEngineer",
                "policies": [FullDevOpsTeamResourcesPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "NetworkAdministrator",
                "policies": [FullNetworkActionsPolicy,FullNetworkTeamResourcesPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "NetworkAuditor",
                "policies": [ReadNetworkActionsPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "PlatformAdministrator",
                "policies": [FullIAMPolicy, FullAccountPolicy, FullOrganizationsPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "PlatformAuditor",
                "policies": [ReadIAMPolicy, ReadAccountPolicy, ReadOrganizationsPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "SecurityAdministrator",
                "policies": [FullAllExceptBillingPolicy],
                "permissions_boundary": FullAllExceptBillingPolicy,
            },
            {
                "name": "SecurityAuditor",
                "policies": [DescribeAllExceptBillingPolicy,GetAllExceptBillingPolicy,ListAllExceptBillingPolicy],
                "permissions_boundary": None,
            },
        ]

        for role in roledict:
            iam.Role(
                self, role["name"], 
                assumed_by=iam.ServicePrincipal('iam.amazonaws.com'),
                description=role["name"] + "description", 
                external_id=None, 
                external_ids=None, 
                inline_policies=None, 
                managed_policies=role["policies"],
                max_session_duration=core.Duration.seconds(43200),
                path=None,
                permissions_boundary=role["permissions_boundary"], 
                role_name=role["name"]
            )