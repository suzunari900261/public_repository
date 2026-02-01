#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_python.frontend_stack import FrontendStack
from cdk_python.backend_stack import BackendStack

app = cdk.App()

env = cdk.Environment(
    account=cdk.Aws.ACCOUNT_ID,
    region=cdk.Aws.REGION,
)

FrontendStack(app, "cdk-portfolio-suzuki-FrontendStack", env=env)
BackendStack(app, "cdk-portfolio-suzuki-BackendStack", env=env)

app.synth()
