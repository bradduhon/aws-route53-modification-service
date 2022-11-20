#!/usr/bin/env python3

import boto3
import json
import os
import signal
from urllib.request import build_opener, HTTPHandler, Request
from requests_aws4auth import AWS4Auth
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


def send_response(event, context, response_status, response_data):
    response_body = json.dumps({
        "Status": response_status,
        "Reason": f"Details can be found in CloudWatch Logs: {context.log_stream_name}",
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event.get("StackId"),
        "RequestId": event.get("RequestId"),
        "LogicalResourceId": event.get("LogicalResourceId"),
        "Data": response_data
    })
    
    logger.info(f"Resonse Body: {response_body}")
    
    opener = build_opener(HTTPHandler)
    request = Request(event.get("ResponseURL"), data=response_body.encode("utf-8"))
    request.add_header("Content-Type", "")
    request.add_header("Content-Length", len(response_body))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    
    logger.info(f"Status Code: {response.getcode()}")
    logger.info(f"Status Message: {response.msg}")


def create_subscriptions():
    SNS = boto3.client("sns")
    email_addresses = os.environ.get("ApproverEmails").split(',')
    logger.debug(email_addresses)
    for email_address in email_addresses:
        SNS.subscribe(
            TopicArn=os.environ.get("ApproversTopicArn"),
            Protocol='email',
            Endpoint=email_address.strip(),
            Attributes={
                'FilterPolicy': json.dumps({
                    "approver": [email_address]
                    })
            }
        )
    
    return "SUCCESS", {}


def delete_subscriptions():
    SNS = boto3.client("sns")
    
    response = SNS.list_subscriptions().get("Subscriptions")
    
    for subscription in response:
        if subscription.get("TopicArn") == os.environ.get("ApproversTopicArn"):
    
            SNS.unsubscribe(
                SubscriptionArn=subscription.get("SubscriptionArn")
            )
    return "SUCCESS", {}


@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug(f'Event: {event}')
    
    signal.alarm(int((context.get_remaining_time_in_millis() / 1000) - 1))
    # try:
    logger.info(f"Request Received: {event}")
    if event.get("RequestType") == "Create":
        logger.info("Create Resource Request")
        status, data = create_subscriptions()
        logger.info(f"Status: {status}")
        send_response(event, context, status, data)
    elif event.get("RequestType") == "Update":
        send_response(event, context, "SUCCESS", {"Message": "Resource update successful!"})
    elif event.get("RequestType") == "Delete":
        status, data = delete_subscriptions()
        send_response(event, context, status, data)
    else:
        logger.info("Unanticipated Event Type")
        send_response(event, context, "SUCCESS", {"Message": "Unanticipated EventType"})
    # except Exception as e:
    #     logger.error(e)
    #     send_response(event, context, "SUCCESS", {"Message": "Unanticipated Exception Encountered"})
