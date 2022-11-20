#!/usr/bin/env python3

import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    
    if all(x.get('decision') == 'approved' for x in event.get('Approvals').get('Status')):
        return 'Approved'
    else:
        return 'Rejected'
