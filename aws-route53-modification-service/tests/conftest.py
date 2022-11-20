import pytest
import yaml
import os



@pytest.fixture(autouse=True, scope='session')
def configuration(request):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    with open(f"{dir_path}/test_data.yaml") as f:
        data = yaml.safe_load(f)
    
    return data.get("test-profile")
    