#!/usr/bin/env python3
import os

import aws_cdk as cdk

from thirteen_tech_web.thirteen_tech_web_stack import ThirteenTechWebStack


app = cdk.App()
ThirteenTechWebStack(
    app,
    "ThirteenTechWebStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
