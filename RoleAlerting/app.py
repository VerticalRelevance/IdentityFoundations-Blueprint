#!/usr/bin/env python3

from aws_cdk import core

from rolealerting.role_alerting import RoleAlertingSCStack

app = core.App()
RoleAlertingSCStack(app,"role-alerting")
app.synth()
