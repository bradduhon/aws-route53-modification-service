import boto3
import json
import pytest
import requests
from .fixtures import *

from requests_aws4auth import AWS4Auth


def get_aws_auth(*, aws_profile, aws_region):
    session = boto3.session.Session(profile_name=aws_profile)
    aws_credentials = session.get_credentials()
    return AWS4Auth(
        region=aws_region,
        service='execute-api',
        refreshable_credentials=aws_credentials
    )
    


@pytest.mark.usefixtures("api_gateway_url", "aws_credentials_profile", "route53_request", "aws_region")
def test_route53_request_valid(api_gateway_url, aws_credentials_profile, route53_request, aws_region):
    auth = get_aws_auth(
        aws_profile=aws_credentials_profile,
        aws_region=aws_region
    )
    
    url = api_gateway_url
    
    if 'https://' not in url:
        url = f'https://{url}'
    
    response = requests.post(
        url=f"{url}/route53",
        auth=auth,
        data=json.dumps(route53_request)
    )
    
    print(response.status_code)
    print(response.text)
    
    assert response.status_code == 200
    
    