#!/usr/bin/env python3

import os
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    
    return os.environ.get("ApproverEmails").split(',')