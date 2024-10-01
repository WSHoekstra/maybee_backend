#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from maybee_backend.models.core_models import Observation, ObservationCreate

from tests.statics import TEST_ENVIRONMENT_ID, TEST_USER_USERNAME, TEST_USER_PASSWORD, TEST_ARM_ID, TEST_ACTION_ID
from tests.endpoints.test_core_api_functionality import get_auth_token
from tests.validate_dataclass_object import validate_dataclass_object, Plurality


# Test create observation with auth -> should succeed
@pytest.mark.usefixtures("user", "environment", "arm", "action")
def test_create_observation(client: TestClient):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.post(
        f"/environments/{TEST_ENVIRONMENT_ID}/observations/", headers={"Authorization": f"Bearer {token}"},
        params={
            "environment_id" : TEST_ENVIRONMENT_ID, 
            "action_id" : TEST_ACTION_ID, 
            "arm_id": TEST_ARM_ID, 
            "reward": 1.0
            }
    )
    print(response.content)
    assert response.status_code == 200
    is_valid, result = validate_dataclass_object(response.json(), Observation)
    assert is_valid, f"Invalid observation data: {result}"



# Test create observations in batch with auth -> should succeed
@pytest.mark.usefixtures("user", "environment", "arm", "action")
def test_create_observations(client: TestClient):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.post(
        url=f"/environments/{TEST_ENVIRONMENT_ID}/observations/batch", 
        headers={"Authorization": f"Bearer {token}"},
        json=[{
                "environment_id" : TEST_ENVIRONMENT_ID, 
                "action_id" : TEST_ACTION_ID, 
                "arm_id": TEST_ARM_ID, 
                "reward": 1.0
            },
            {
                "environment_id" : TEST_ENVIRONMENT_ID, 
                "action_id" : TEST_ACTION_ID, 
                "arm_id": TEST_ARM_ID, 
                "reward": 0.0
            }]
    )
    print(response.content)
    assert response.status_code == 200
    is_valid, result = validate_dataclass_object(response.json(), Observation, plurality=Plurality.PLURAL)
    assert is_valid, f"Invalid observation data: {result}"