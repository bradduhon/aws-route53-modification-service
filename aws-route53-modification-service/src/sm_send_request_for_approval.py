#!/usr/bin/env python3

import base64
import boto3
import json
import os
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


def formatted_approval_email(*, task_token, request):
    url = os.environ.get("ApproversReturnURL")
    if 'https://' not in url:
        url = 'https://' + url
        
    return """
A request has been made to modify the following domain: {hosted_zone}
{content}
{divider}
{divider}
APPROVE
{URL}?token={task_token}&decision=approved
{divider}
REJECT
{URL}?token={task_token}&decision=approved
    """.format(
        task_token=base64.b64encode(bytes(task_token, 'utf-8')).decode('utf-8'),
        URL=url,
        content="\t\n".join([f"{key}: {str(value)}\n" + "-"*100 for key, value in request.items()]),
        divider="#"*100,
        hosted_zone=request.get('hosted_zone_name')
    )


@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    SNS = boto3.client('sns')
    
    task_token = event.get('taskToken')
    request = json.loads(event.get('request'))
    approver = event.get('approver')
    
    logger.info(f'Approver: {approver}')
    response = SNS.publish(
        TopicArn=os.environ.get('ApproversTopicArn'),
        Message=formatted_approval_email(task_token=task_token, request=request),
        Subject='Approval Required for Route53 Modification.',
        MessageAttributes={
            'approver': {
                'DataType': 'String',
                'StringValue': approver
            }
        }
    )
    
    logger.debug(f'SNS Response: {response}')
