#!/usr/bin/env python3

from aws_cdk import core

from identity_solution.identity_solution_stack import IdentitySolutionStack


app = core.App()
IdentitySolutionStack(app, "identity-solution")

app.synth()
