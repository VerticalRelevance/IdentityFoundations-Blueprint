#!/usr/bin/env python3

from aws_cdk import core

from identity_solution.basic_roles import BasicRolesStack


app = core.App()
BasicRolesStack(app, "basic-roles")

app.synth()
