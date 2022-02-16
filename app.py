#!/usr/bin/env python3

from aws_cdk import core

#from identity_solution.basic_roles import BasicRolesStack
#from identity_solution.brpg_lambda import BRPGStack
from identity_solution.sc_lambda import BRPGCatalogStack

app = core.App()
BRPGCatalogStack(app,"brpg-catalog")
app.synth()
