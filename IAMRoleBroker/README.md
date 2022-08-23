
# Identity Solutions Blueprint

## Code Walkthrough

### app.py
 
app.py initializes the CDK stack and calls the IAMRoleBrokerCatalogStack class with an input value of the app intialization and the name of the cdk stack

### sc_lambda.py

sc_lambda.py includes 2 classes:

* IAMRoleBrokerCatalogStack
* * Creates a s3 bucket for the lambda code from the lambda_function directory, and uploads it.
* * Creates a policy and role for the lambda execution
* * Creates the layers for Policy Sentry and CfnResponse
* * Creates the portfolio and product for the actual Service Catalog Product, with the cloudformation template coming from the IAMRoleBrokerLambda Class 

* IAMRoleBrokerLambda
* * Creates the lambda function from the lambda_function directory, with environment variables set to the inputs of the service catalog product

### lambda_function/lambda_code.py

Generates the list of actions via PolicySentry and creates the role and policy, as specified via the service catalog product's inputs

### lambda_function/action_category_config.json

One of the inputs of the service catalog products is the "categories" of actions the role should have access to. I.e. Kubernetes, storage, logging, IAM etc.

This must be pre-configured with the client before rollout

## Setup

The `cdk.json` file tells the CDK Toolkit how to execute the app.

This project is set up like a standard Python project.  The initialization process also creates
a virtualenv within this project, stored under the .venv directory.  To create the virtualenv
it assumes that there is a `python3` executable in your path with access to the `venv` package.
If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv
manually once the init process completes.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

You can now begin exploring the source code, contained in the hello directory.
There is also a very trivial test included that can be run like this:

```
$ pytest
```

To add additional dependencies, for example other CDK libraries, just add to
your requirements.txt file and rerun the `pip install -r requirements.txt`
command.

## Tutorial  
See [this useful workshop](https://cdkworkshop.com/30-python.html) on working with the AWS CDK for Python projects.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
