#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from maybee_backend.models.core_models import Environment
from tests.endpoints.test_core_api_functionality import get_auth_token
from tests.validate_dataclass_object import validate_dataclass_object

from tests.statics import (
                           TEST_USER_PASSWORD, 
                           TEST_USER_USERNAME, 
                           TEST_ADMIN_USER_USERNAME, 
                           TEST_ENVIRONMENT_ID,)


# Test get environments (authenticated) -> should succeed
@pytest.mark.usefixtures("user", "environment")
def test_get_environments_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        "/environments/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Test create environment (as non-admin user) -> should fail
@pytest.mark.usefixtures("user")
def test_create_environment_non_admin(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.post(
        "/environments/",
        json={"environment_description": "Test Environment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


# Test create environment (as admin user) -> should succeed
@pytest.mark.usefixtures("admin_user")
def test_create_environment_admin(client):
    token = get_auth_token(
        client=client, username=TEST_ADMIN_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.post(
        "/environments/",
        json={"environment_description": "Test Environment"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    is_valid, result = validate_dataclass_object(response.json(), Environment)
    assert is_valid, f"Invalid environment data: {result}"


# Test update environment (as admin user) -> should succeed
@pytest.mark.usefixtures("admin_user", "environment")
def test_update_environment_admin(client, session):
    token = get_auth_token(
        client=client, username=TEST_ADMIN_USER_USERNAME, password=TEST_USER_PASSWORD
    )

    updated_description = "Updated description"
    updated_bandit_type = "ucb1"

    update_response = client.put(
        f"/environments/{TEST_ENVIRONMENT_ID}",
        json={
            "environment_description": updated_description,
            "bandit_type": updated_bandit_type
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    updated_env = update_response.json()
    assert updated_env["environment_description"] == updated_description
    assert updated_env["bandit_type"] == updated_bandit_type


# Test update environment (as non-admin user) -> should fail
@pytest.mark.usefixtures("user", "environment")
def test_update_environment_non_admin(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.put(
        f"/environments/{TEST_ENVIRONMENT_ID}",  # Assuming environment with id 1 exists
        json={"environment_description": "Attempt to Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
