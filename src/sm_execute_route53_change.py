#!/usr/bin/env python3

import boto3
import json
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


def create_hosted_zone_record(
    *,
    record_type: str,
    hosted_zone_name: str,
    hosted_zone_id: str,
    subdomain: str,
    is_alias: bool,
    value: str,
    ttl: int,
    region: str
) -> dict:
    
    r53 = boto3.client("route53")
    
    record_change = {
        'Action': 'CREATE',
        'ResourceRecordSet': {
            'Name': f'{subdomain}.{hosted_zone_name}',
            'Type': record_type,
            # 'Failover': 'PRIMARY'|'SECONDARY',
            # 'MultiValueAnswer': True|False,
            'TTL': int(ttl),
            'ResourceRecords': [
                {
                    'Value': value
                },
            ]
            # 'AliasTarget': {
            #     'HostedZoneId': hosted_zone_id,
            #     'DNSName': 'string',
            #     'EvaluateTargetHealth': False
            # }
        }
    }
    logger.debug(f'Record Change Request: {record_change}')
    response = r53.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            'Changes': [
                record_change
            ]
        }
    )
    
    return response.get("ChangeInfo")


@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    
    request = json.loads(event.get('request'))

    try:
        response = create_hosted_zone_record(**request)
        logger.debug(f'R53 Create Record Response: {response}')
    except Exception as e:
        logger.error(e)
