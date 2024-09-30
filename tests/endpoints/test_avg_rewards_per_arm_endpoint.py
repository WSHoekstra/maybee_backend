#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from maybee_backend.models.core_models import AvgRewardsPerArm

from tests.endpoints.test_core_api_functionality import get_auth_token
from tests.validate_dataclass_object import validate_dataclass_object, Plurality
from tests.statics import TEST_ENVIRONMENT_ID, TEST_USER_USERNAME, TEST_USER_PASSWORD


# Test get avg rewards with authentication -> should succeed
@pytest.mark.usefixtures("user", "environment", "arm", "avgrewardsperarm")
def test_get_avg_rewards_per_arm_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms/average_rewards", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    response_data = response.json()
    is_valid, result = validate_dataclass_object(data=response_data, 
                                                 dataclass=AvgRewardsPerArm, 
                                                 plurality=Plurality.PLURAL)
    assert is_valid, f"Invalid avg_rewards_per_arm data: {result}"
