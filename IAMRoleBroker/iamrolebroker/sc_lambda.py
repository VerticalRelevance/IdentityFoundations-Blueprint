from fileinput import filename
import os
from pyclbr import Function
from sqlite3 import Timestamp
import time
from zipfile import ZipFile
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_assets as s3_assets,
    aws_s3_deployment as s3deploy,
    aws_lambda as lambda_,
    aws_servicecatalog as servicecatalog,
    aws_cloudformation as cloudformation,
    core
)

class IAMRoleBrokerLambda(servicecatalog.ProductStack):
    def __init__(self, scope, id, ps_layer, cfnresponse_layer, lambda_code_bucket, lambda_code_bucket_key, IAMRoleBrokerLambdaExecutionRole):
        super().__init__(scope, id)

        access_level_parameter = core.CfnParameter(self, 
            "Access Level",
            type="String",
            description="What access level of role are you provisioning? ('Read', 'Write', 'List', 'Permisssions management', or 'Tagging')",
            default="Write").value_as_string

        team_name_parameter = core.CfnParameter(self,
            "Team Name",
            type="String",
            description="What team's resources does your role need access to? ('Security', 'QA', 'IAM')",
            default="QA").value_as_string

        action_category_parameter = core.CfnParameter(self,
            "Action Category",
            type="String",
            description="What category of resources does your role need access to? ('Kubernetes', 'Storage', 'Logging', 'IAM')",
            default="Logging").value_as_string

        role_or_policy_parameter = core.CfnParameter(self,
            "Role or Policy",
            type="String",
            description="Would you like a role and a policy generated, or just a policy? ('Role', 'Policy')",
            default="Role").value_as_string

        IAMRoleBrokerLambda=lambda_.Function(self,
            "IAMRoleBrokerLambda",
            role=IAMRoleBrokerLambdaExecutionRole,
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_code.lambda_handler",
            code=lambda_.Code.from_bucket(
                bucket=lambda_code_bucket,
                key=lambda_code_bucket_key
            ),
            environment={
                "ACCESS_LEVEL": access_level_parameter,
                "TEAM_NAME": team_name_parameter,
                "ACTION_CATEGORY": action_category_parameter,
                "ROLE_OR_POLICY": role_or_policy_parameter
            },
            layers=[
                ps_layer, 
                cfnresponse_layer
            ]
        )

        cloudformation.CfnCustomResource(self, "IAMRoleBrokerCfnCustomResource",
            service_token=IAMRoleBrokerLambda.function_arn
        )

        core.CfnOutput(self, "IAMRoleBrokerLambdaARN", value=IAMRoleBrokerLambda.function_arn)

class IAMRoleBrokerCatalogStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code_source_path = "lambda_function"
        lambda_code_bucket_name = "iamrolebroker-lambda-code-bucket"
        lambda_code_bucket_key = "lambda_code.zip"
        lambda_code_bucket_key2 = "lambda_code2.zip"

        zf = ZipFile(lambda_code_bucket_key, "w")
        for dirname, subdirs, files in os.walk(lambda_code_source_path):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()

        ZipFile(lambda_code_bucket_key2, mode='w').write(lambda_code_bucket_key)
        
        lambda_code_bucket = s3.Bucket(self, lambda_code_bucket_name, bucket_name=lambda_code_bucket_name)
        s3deploy.BucketDeployment(self, "IAMRoleBrokerLambdaCodeSource",
            sources=[s3deploy.Source.asset(lambda_code_bucket_key2)],
            destination_bucket=lambda_code_bucket,
        )

        lambda_execution_role_name = "IAMRoleBrokerLambdaExecutionRole"
        lambda_execution_policy_name = "IAMRoleBrokerLambdaExecutionPolicy"

        IAMRoleBrokerLambdaExecutionPolicy = iam.ManagedPolicy(
            self, lambda_execution_policy_name,
            managed_policy_name=lambda_execution_policy_name,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "iam:GetPolicy",
                        "iam:CreatePolicy",
                        "iam:GetRole",
                        "iam:CreateRole",
                        "iam:AttachRolePolicy",
                        "ssm:GetParameters",
                        "ssm:PutParameters"
                    ],
                    resources=["*"],
                )
            ]
        )

        IAMRoleBrokerLambdaExecutionRole = iam.Role(
            self, lambda_execution_role_name, 
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[IAMRoleBrokerLambdaExecutionPolicy],
            max_session_duration=core.Duration.seconds(43200),
            path=None,
            role_name=lambda_execution_role_name
        )

        __dirname = os.getcwd()

        ps_layer = lambda_.LayerVersion(self, "PolicySentryLayer",
            code=lambda_.Code.from_asset(os.path.join(__dirname, "policy_sentry.zip")),
            compatible_architectures=[lambda_.Architecture.X86_64, lambda_.Architecture.ARM_64],
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )
        
        cfnresponse_layer = lambda_.LayerVersion(self, "CfnResponseLayer",
            code=lambda_.Code.from_asset(os.path.join(__dirname, "cfnresponse.zip")),
            compatible_architectures=[lambda_.Architecture.X86_64, lambda_.Architecture.ARM_64],
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )

        portfolio = servicecatalog.Portfolio(
            self, "IAMRoleBrokerPortfolio",
            display_name="IAMRoleBrokerPortfolio",
            provider_name=" "
        )

        product = servicecatalog.CloudFormationProduct(self, "IAMRoleBroker",
            product_name="IAMRoleBroker",
            owner=" ",
            product_versions=[servicecatalog.CloudFormationProductVersion(
                product_version_name="v0",
                cloud_formation_template=servicecatalog.CloudFormationTemplate.from_product_stack(
                    IAMRoleBrokerLambda(self, "IAMRoleBrokerLambda", ps_layer, cfnresponse_layer, lambda_code_bucket, lambda_code_bucket_key,IAMRoleBrokerLambdaExecutionRole)
                )
            )
            ]
        )
        portfolio.add_product(product)            