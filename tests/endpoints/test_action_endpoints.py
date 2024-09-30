#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient

from maybee_backend.models.core_models import Action

from tests.statics import TEST_USER_USERNAME, TEST_USER_PASSWORD, TEST_ENVIRONMENT_ID
from tests.endpoints.test_core_api_functionality import get_auth_token
from tests.validate_dataclass_object import validate_dataclass_object


# Test create action with auth -> should succeed
@pytest.mark.usefixtures("user", "environment", "userenvironmentlink", "arm", "avgrewardsperarm")
def test_create_action(client: TestClient):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.post(
        f"/environments/{TEST_ENVIRONMENT_ID}/actions", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    is_valid, result = validate_dataclass_object(response.json(), Action)
    assert is_valid, f"Invalid action data: {result}"
