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

class BRPGLambda(servicecatalog.ProductStack):
    def __init__(self, scope, id, ps_layer, cfnresponse_layer, brpg_lambda_code_bucket, brpg_lambda_code_bucket_key, BRPGLambdaExecutionRole):
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

        BRPGLambda=lambda_.Function(self,
            "BRPGLambda",
            role=BRPGLambdaExecutionRole,
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="lambda_function.brpg_lambda_code.lambda_handler",
            code=lambda_.Code.from_bucket(
                bucket=brpg_lambda_code_bucket,
                key=brpg_lambda_code_bucket_key
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

        cloudformation.CfnCustomResource(self, "BRPGCfnCustomResource",
            service_token=BRPGLambda.function_arn
        )

        core.CfnOutput(self, "BRPGLambdaARN", value=BRPGLambda.function_arn)

class BRPGCatalogStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        brpg_lambda_code_source_path = "lambda_function"
        brpg_lambda_code_bucket_name = "brpg-lambda-code-bucket"
        brpg_lambda_code_bucket_key = "brpg_lambda_code.zip"
        brpg_lambda_code_bucket_key2 = "brpg_lambda_code2.zip"

        zf = ZipFile(brpg_lambda_code_bucket_key, "w")
        for dirname, subdirs, files in os.walk(brpg_lambda_code_source_path):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()

        ZipFile(brpg_lambda_code_bucket_key2, mode='w').write(brpg_lambda_code_bucket_key)
        
        brpg_lambda_code_bucket = s3.Bucket(self, brpg_lambda_code_bucket_name, bucket_name=brpg_lambda_code_bucket_name)
        s3deploy.BucketDeployment(self, "BRPGLambdaCodeSource",
            sources=[s3deploy.Source.asset(brpg_lambda_code_bucket_key2)],
            destination_bucket=brpg_lambda_code_bucket,
        )

        brpg_lambda_execution_role_name = "BRPGLambdaExecutionRole"
        brpg_lambda_execution_policy_name = "BRPGLambdaExecutionPolicy"

        BRPGLambdaExecutionPolicy = iam.ManagedPolicy(
            self, brpg_lambda_execution_policy_name,
            managed_policy_name=brpg_lambda_execution_policy_name,
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

        BRPGLambdaExecutionRole = iam.Role(
            self, brpg_lambda_execution_role_name, 
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[BRPGLambdaExecutionPolicy],
            max_session_duration=core.Duration.seconds(43200),
            path=None,
            role_name=brpg_lambda_execution_role_name
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
            self, "BRPGPortfolio",
            display_name="BRPGPortfolio",
            provider_name=" "
        )

        product = servicecatalog.CloudFormationProduct(self, "BRPGLambdaProduct",
            product_name="BRPGLambda",
            owner=" ",
            product_versions=[servicecatalog.CloudFormationProductVersion(
                product_version_name="v0",
                cloud_formation_template=servicecatalog.CloudFormationTemplate.from_product_stack(
                    BRPGLambda(self, "BRPGLambda", ps_layer, cfnresponse_layer, brpg_lambda_code_bucket, brpg_lambda_code_bucket_key,BRPGLambdaExecutionRole)
                )
            )
            ]
        )
        portfolio.add_product(product)            