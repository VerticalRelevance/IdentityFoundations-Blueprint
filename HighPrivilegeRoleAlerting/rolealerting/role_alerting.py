from cgi import test
import email
from fileinput import filename
import os
from pyclbr import Function
from sqlite3 import Timestamp
from ssl import _create_default_https_context
import time
from zipfile import ZipFile
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    #aws_s3_assets as s3_assets,
    aws_s3_deployment as s3deploy,
    aws_lambda as lambda_,
    aws_sqs as sqs,
    aws_events as events,
    aws_servicecatalog as servicecatalog,
    aws_cloudformation as cloudformation,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_stepfunctions as sfn,
    core
)

class RoleAlertingSCStack(core.Stack):

    def uploadLambdaCode(self,lambda_code_source_path,lambda_code_bucket_name,lambda_code_bucket_key,lambda_code_bucket_zipped_key):
        zf = ZipFile(lambda_code_bucket_key, "w")
        for dirname, subdirs, files in os.walk(lambda_code_source_path):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))
        zf.close()

        ZipFile(lambda_code_bucket_zipped_key, mode='w').write(lambda_code_bucket_key)
        
        lambda_code_bucket = s3.Bucket(self, lambda_code_bucket_name, bucket_name=lambda_code_bucket_name)
        s3deploy.BucketDeployment(self, "LambdaCodeSource",
            sources=[s3deploy.Source.asset(lambda_code_bucket_zipped_key)],
            destination_bucket=lambda_code_bucket,
        )

        __dirname = os.getcwd()

        pytz_layer = lambda_.LayerVersion(self, "PytzLayer",
            code=lambda_.Code.from_asset(os.path.join(__dirname, "layers/pytz.zip")),
            compatible_architectures=[lambda_.Architecture.X86_64, lambda_.Architecture.ARM_64],
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )

        tzlocal_layer = lambda_.LayerVersion(self, "TzlocalLayer",
            code=lambda_.Code.from_asset(os.path.join(__dirname, "layers/tzlocal.zip")),
            compatible_architectures=[lambda_.Architecture.X86_64, lambda_.Architecture.ARM_64],
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )
        
        return {
            "lambda_code_bucket": lambda_code_bucket,
            "lambda_code_bucket_key": lambda_code_bucket_key,
            "pytz_layer": pytz_layer,
            "tzlocal_layer": tzlocal_layer
        }

    def createLambdaExecutionRole(self,lambda_execution_role_name):

        lambda_execution_policy_name = "{}Policy".format(lambda_execution_role_name)

        LambdaExecutionPolicy = iam.ManagedPolicy(
            self, lambda_execution_policy_name,
            managed_policy_name=lambda_execution_policy_name,
            statements=[
                iam.PolicyStatement(effect= 
                    iam.Effect.ALLOW,
                    actions= [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "sns:Publish"
                    ],
                    resources=["*"],
                )
            ]
        )

        LambdaExecutionRole = iam.Role(
            self, lambda_execution_role_name, 
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[LambdaExecutionPolicy],
            max_session_duration=core.Duration.seconds(43200),
            path=None,
            role_name=lambda_execution_role_name
        )

        return LambdaExecutionRole  

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #CREATES LAMBDA EXECUTION ROLE & POLICY
        lambda_execution_role_name = "RoleAlertingLambdaExecutionRole"
        lambda_execution_role = RoleAlertingSCStack.createLambdaExecutionRole(self,lambda_execution_role_name)

        #UPLOADS SOURCE CODE TO S3 AND CREATES LAYERS
        lambda_code_source_path = "lambda_function"
        lambda_code_bucket_name = "rolealerting-lambda-code-bucket"
        lambda_code_bucket_key = "rolealerting_lambda_code.zip"
        lambda_code_bucket_zipped_key = "rolealerting_lambda_code_zipped.zip"
        lambda_upload_response = RoleAlertingSCStack.uploadLambdaCode(self,
            lambda_code_source_path,
            lambda_code_bucket_name,
            lambda_code_bucket_key,
            lambda_code_bucket_zipped_key
        )   

        product_name = "RoleAlerter"
        portfolio_name = "{}Portfolio".format(product_name)

        portfolio = servicecatalog.Portfolio(
            self, portfolio_name,
            display_name=portfolio_name,
            provider_name=" "
        )

        product = servicecatalog.CloudFormationProduct(self, product_name,
            product_name=product_name,
            owner=" ",
            product_versions=[servicecatalog.CloudFormationProductVersion(
                product_version_name="v0",
                cloud_formation_template=servicecatalog.CloudFormationTemplate.from_product_stack(
                    RoleAlertingStack(self, "RoleAlerting", lambda_execution_role, lambda_upload_response)
                )
            )
            ]
        )
        portfolio.add_product(product) 

class RoleAlertingStack(servicecatalog.ProductStack):
    def createParameters(self):
        role_name_parameter = core.CfnParameter(self, 
            "Role Name",
            type="String",
            description="What role would you like to be monitored?",
            default="testrole123"
        ).value_as_string
        
        email_parameter = core.CfnParameter(self, 
            "Email",
            type="String",
            description="Where would you like alerts to be sent to?", # (Comma seperated list, such as 'joe@abc.com,bob@abc.com')",
            default="ebegalka@verticalrelevance.com"
        ).value_as_string

        # email_parameter2 = core.CfnParameter(self, 
        #     "Email2",
        #     type="String",
        #     description="Where would you like alerts to be sent to?", # (Comma seperated list, such as 'joe@abc.com,bob@abc.com')",
        #     default="ethanbegalka@gmail.com"
        # ).value_as_string
        
        return {
            "role_name_parameter" : role_name_parameter,
            "email_parameter": email_parameter,
            # "email_parameter2": email_parameter2
        }

    
    def createTopic(self,email_list):
        topic = sns.Topic(self,"topic2")
        delivered = topic.metric_number_of_notifications_delivered()
        failed = topic.metric_number_of_notifications_failed()
        #x = 1
        for email in email_list:
            #if not email:
                #print("No email included for value {}".format(x))
            #else:
            topic.add_subscription(subscriptions.EmailSubscription(email))
            #x+=1
        #core.CfnOutput(self, "output", value=email)
        return topic.topic_arn

    def createFunction(self,topic_arn,role_name,lambda_execution_role,lambda_code_bucket,lambda_code_bucket_key,pytz_layer,tzlocal_layer):
        lambda_function=lambda_.Function(self,
            "lambda_function",
            #function_name="RoleAlertingLambdaFunction",
            role=lambda_execution_role,
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_code.lambda_handler",
            code=lambda_.Code.from_bucket(
                bucket=lambda_code_bucket,
                key=lambda_code_bucket_key
            ),
            environment={
                "ROLE_NAME": role_name,
                "TOPICARN": topic_arn
            },
            layers = [
                pytz_layer,
                tzlocal_layer
            ]
        )
        return lambda_function

    def createEventRule(self,lambda_function,role_arn):

        rule = events.Rule(self, "rule",
            event_pattern=events.EventPattern(
                detail={
                    "eventSource": [
                        "sts.amazonaws.com"
                    ],
                    "eventName": [
                        "AssumeRole"
                    ],
                    "requestParameters": {
                        "roleArn": [
                            role_arn
                        ]
                    }
                },
                detail_type=[
                    "AWS API Call via CloudTrail",
                    "AWS Console Sign In via CloudTrail"
                ]
            )
        )

        queue = sqs.Queue(self, "RoleAlertingDLQ")

        rule.add_target(targets.LambdaFunction(lambda_function,
            dead_letter_queue=queue,  # Optional: add a dead letter queue
            max_event_age=core.Duration.hours(2),  # Optional: set the maxEventAge retry policy
            retry_attempts=2
        ))
        return ""

    def __init__(self, scope, id, lambda_execution_role, lambda_upload_response):
        super().__init__(scope, id)

        #GETS ROLE NAME TO MAKE ALERT FOR, AND EMAIL TO SEND TO
        parameters_response = RoleAlertingStack.createParameters(self)

        #SNS TOPIC WHICH EMAILS/TEXTS THE PROCESSED MESSAGE
        email_list = [parameters_response["email_parameter"]]#,parameters_response["email_parameter2"]]
        topic_arn = RoleAlertingStack.createTopic(self,email_list)

        #CREATES FUNCTION FOR SENDING MESSAGE TO SNS
        lambda_function = RoleAlertingStack.createFunction(self,
            topic_arn,
            parameters_response["role_name_parameter"],
            lambda_execution_role,
            lambda_upload_response["lambda_code_bucket"],
            lambda_upload_response["lambda_code_bucket_key"],
            lambda_upload_response["pytz_layer"],
            lambda_upload_response["tzlocal_layer"]
        )

        #CLOUD WATCH EVENTS RULE WHICH IS TRIGGERED WHEN ROLE ASSUMED
        account_id = RoleAlertingStack.of(self).account
        role_arn = "arn:aws:iam::{}:role/{}".format(account_id,parameters_response["role_name_parameter"])
        RoleAlertingStack.createEventRule(self,lambda_function,role_arn)