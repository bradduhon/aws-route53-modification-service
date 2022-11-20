import pytest


@pytest.fixture(scope="module")
def api_gateway_url(configuration):
    return configuration.get("infrastructure").get("api-gateway-url")


@pytest.fixture(scope="module")
def aws_credentials_profile(configuration):
    return configuration.get("infrastructure").get("aws-credentials-profile")


@pytest.fixture(scope="module")
def aws_region(configuration):
    return configuration.get("infrastructure").get("aws-region")


@pytest.fixture(scope="module")
def route53_request(configuration):
    return configuration.get("data").get("record-request")
