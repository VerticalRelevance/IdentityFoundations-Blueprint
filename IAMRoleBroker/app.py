#!/usr/bin/env python3

from aws_cdk import core

#from identity_solution.basic_roles import BasicRolesStack
#from identity_solution.brpg_lambda import BRPGStack
from iamrolebroker.sc_lambda import IAMRoleBrokerCatalogStack

app = core.App()
IAMRoleBrokerCatalogStack(app,"iamrolebroker-catalog")
app.synth()
