from aws_cdk import (
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    core
)


class IdentitySolutionStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        print("Hello World")

        FullIAMPolicy = iam.ManagedPolicy(
            self, "FullIAMPolicy",
            description="Full-Control Access to IAM resources, Read Organizations",
            document=None,
            groups=None,
            managed_policy_name="FullIAMPolicy",
            path=None,
            roles=None,
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
            users=None
        )

        ReadIAMPolicy = iam.ManagedPolicy(
            self, "ReadIAMPolicy",
            description="Read Access to IAM resources",
            document=None,
            groups=None,
            managed_policy_name="ReadIAMPolicy",
            path=None,
            roles=None,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "iam:List*",
                        "iam:Get*"
                    ],
                    resources=["*"])
            ],
            users=None
        )

        FullBillingPolicy = iam.ManagedPolicy(
            self, "FullBillingPolicy",
            description="Full-Control Access to Billing resources",
            document=None,
            groups=None,
            managed_policy_name="FullBillingPolicy",
            path=None,
            roles=None,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "aws-portal:*"
                    ],
                    resources=["*"])
            ],
            users=None
        )

        ReadBillingPolicy = iam.ManagedPolicy(
            self, "ReadBillingPolicy",
            description="Read Access to Billing resources",
            document=None,
            groups=None,
            managed_policy_name="ReadBillingPolicy",
            path=None,
            roles=None,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "aws-portal:View*"
                    ],
                    resources=["*"])
            ],
            users=None
        )

        BreakGlassPolicy = iam.ManagedPolicy(
            self, "BreakGlassPolicy",
            description="Dedicated to exclusively emergency situations, requires approval",
            document=None,
            groups=None,
            managed_policy_name="BreakGlassPolicy",
            path=None,
            roles=None,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= ["*"],
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid= "DenyBilling",
                    actions= [
                        "aws-portal:*"
                    ],
                    resources=["*"])
            ],
            users=None
        )    

        CloudAdministratorPolicy = iam.ManagedPolicy(
            self, "CloudAdministratorPolicy",
            description="Dedicated to exclusively emergency situations, requires approval",
            document=None,
            groups=None,
            managed_policy_name="CloudAdministratorPolicy",
            path=None,
            roles=None,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= ["*"],
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    actions= [
                        "aws-portal:*"
                    ],
                    resources=["*"]),
                iam.PolicyStatement(effect= 
                    iam.Effect.DENY,
                    sid = "DenyBilling",
                    actions= [
                        "aws-portal:*"
                    ],
                    resources=["*"])
            ],
            users=None
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
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "CloudAdministrator",
                "policies": [CloudAdministratorPolicy],
                "permissions_boundary": CloudAdministratorPolicy,
            },
            {
                "name": "LOBx-DevOpsEngineer",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "NetworkAdministrator",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "NetworkAuditor",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "PlatformAdministrator",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "PlatformAuditor",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "SecurityAdministrator",
                "policies": [BreakGlassPolicy],
                "permissions_boundary": None,
            },
            {
                "name": "SecurityAuditor",
                "policies": [BreakGlassPolicy],
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