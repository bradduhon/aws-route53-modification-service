#!/usr/bin/env python3

import base64
import boto3
import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler.api_gateway import Response

from common.exceptions import BadInput


logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


def return_html_response_format():
    
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <link rel="stylesheet" href="style.css">
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home</title>
</head>
<body>
    <!--Header-->
    <header>
        <h1>Route53 Request Response</h1>
    </header>
    <!--Main Body-->
    <main>
        <p>{text}</p>
    </main>
</body>
</html>
"""


@app.get("/route53/response")
@tracer.capture_method   
def process_approval_response():
    token: str = app.current_event.get_query_string_value(name="token", default_value="")
    decision: str = app.current_event.get_query_string_value(name="decision", default_value="")
    
    token = base64.urlsafe_b64decode(token).decode()
    
    SFN = boto3.client("stepfunctions")
    try:
        response = SFN.send_task_success(
            taskToken=token,
            output=json.dumps({
                "decision": decision
            })
        )
        logger.debug(f'StateMachine Response: {response}')
    
        return Response(
            status_code=200,
            content_type='text/html',
            body=return_html_response_format().format(text="Thank you for submitting your decission for this route53 request.")
        )
    except Exception as e:
        logger.error(e)
        return Response(
            status_code=200,
            content_type='text/html',
            body=return_html_response_format().format(text="Request token has expired.")
        )


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    return app.resolve(event, context)