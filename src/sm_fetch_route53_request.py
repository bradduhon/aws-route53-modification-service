#!/usr/bin/env python3

import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics()

logger = Logger()
tracer = Tracer()

@metrics.log_metrics
@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    metrics.add_metric(name="StateMachineExecution", unit=MetricUnit.Count, value=1)
    
    bucket = event.get("detail").get("bucket").get("name")
    obj_key = event.get("detail").get("object").get("key")
    
    S3 = boto3.client("s3")
    data = S3.get_object(
        Bucket=bucket,
        Key=obj_key
    ).get('Body').read()
    
    logger.debug(f"Request Contents: {data}")
    
    return {
        "request": data,
        "execution": event.get("execution")
    }
    
    