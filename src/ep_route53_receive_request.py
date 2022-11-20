#!/usr/bin/env python3


import boto3
import json
import os
import time
from uuid import uuid4
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler.api_gateway import Response

from common.exceptions import BadInput


logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()


def validate_requester_source_permissions(*, account_id: str, hosted_zone_id: str, hosted_zone_name: str)-> bool:
    SM = boto3.client('secretsmanager')
    config_arn = os.environ.get('Configuration')
    
    config = SM.get_secret_value(
        SecretId=config_arn
    ).get('SecretString')
    
    logger.debug(f'Configuration: {config}')
    
    if account_id in config:
        if any(x in [hosted_zone_id, hosted_zone_name] for x in config.get(account_id)):
            return True
        else:
            return False
    else:
        return True


def validate_hosted_zone_domain_name_governance(*, hosted_zone_domain_name):
    if hosted_zone_domain_name[-1] != '.':
        logger.error('Malformed HostedZone Name format, missing trailing "."')
        return Response(
            status_code=400,
            content_type='application/json',
            body=json.dumps({"message": "Malformed HostedZone Name format, missing trailing '.'"})
        )
    
    hosted_zones = get_hosted_zones()
    governance_validation_check = not any(x.get("Name") == hosted_zone_domain_name for x in hosted_zones)
    
    logger.debug(f'HostedZone Governance: {governance_validation_check}')
    
    if governance_validation_check:
        logger.error('HostedZone provided is not governed by this AWS Account.')
        return Response(
            status_code=400,
            content_type='application/json',
            body=json.dumps({"message": "HostedZone provided is not governed by this AWS Account."})
        )
    
    return None


def validate_hosted_zone_record_type(*, record_type):
    record_type_validation = record_type.upper() not in ['A', 'CNAME']
    logger.debug(f'RecordType Validation: {record_type_validation}')
    
    if record_type_validation:
        logger.error("A currently unsupported record type was provided.")
        return Response(
            status_code=400,
            content_type='application/json',
            body=json.dumps({"message": "A currently unsupported record type was provided."})
        )
        
    return None
    


def get_hosted_zones() -> list[dict]:
    r53 = boto3.client("route53")
    hosted_zones = []

    paginator = r53.get_paginator('list_hosted_zones')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        hosted_zones += page.get('HostedZones')
    
    logger.debug(f'HostedZones: {hosted_zones}')

    return hosted_zones


def get_hosted_zone_id(*, hosted_zone_domain_name: str) -> str:
    hosted_zones = get_hosted_zones()
    logger.debug(f'HostedZones: {hosted_zone_domain_name}')
    
    for hosted_zone in hosted_zones:
        if hosted_zone.get("Name") == hosted_zone_domain_name:
            return hosted_zone.get("Id")
    
    logger.debug(f'No Match found for {hosted_zone_domain_name} in Hosted Zones.')


@app.post("/route53")
@tracer.capture_method
def process_route53_request():
    request_data: dict = app.current_event.json_body
    record = request_data.get('record')
    request_record_type = request_data.get('record').get('record_type')
    request_hosted_zone_domain_name = request_data.get('hosted_zone_domain_name')
    
    hzdn_validation = validate_hosted_zone_domain_name_governance(hosted_zone_domain_name=request_hosted_zone_domain_name)
    if hzdn_validation is not None:
        return hzdn_validation
    
    rt_validation = validate_hosted_zone_record_type(record_type=request_record_type)
    if rt_validation is not None:
        return rt_validation
    
    record['hosted_zone_id'] = get_hosted_zone_id(hosted_zone_domain_name=request_hosted_zone_domain_name)
    record['hosted_zone_name'] = request_hosted_zone_domain_name
    
    logger.debug(dir(app.current_event.request_context.identity))
    act_validation = validate_requester_source_permissions(
        account_id=app.current_event.request_context.identity.account_id,
        hosted_zone_id=record['hosted_zone_id'],
        hosted_zone_name=record['hosted_zone_name'])
    
    logger.debug(f'Account Validation: {act_validation}')
    
    if act_validation is False:
        return Response(
            status_code=404,
            content_type='application/json',
            body=json.dumps({
                "message": "You do not have permissions to modify the requested Hosted Zone."
            })
        )
    
    
    logger.debug(f'Request Details: {record}')
    S3 = boto3.client("s3")
    request_id = str(uuid4())
    logger.debug(f'Request Id: {request_id}')
    
    response = S3.put_object(
        Body=json.dumps(record),
        Bucket=os.environ.get("RequestsBucket"),
        Key=f"{request_id}.json"
    )
    
    logger.debug(f'S3 PutObject: {response}')
    
    return Response(
        status_code=200,
        content_type='application/json',
        body=json.dumps({
            "request_id": request_id,
            "timestamp": int(time.time())
        })
    )


# @app.delete("/route53/request")
# @tracer.capture_method
# def process_route53_request():
#     pass
    

# @app.get("/route53/request")
# @tracer.capture_method
# def process_route53_request():
#     pass


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    
    return app.resolve(event, context)