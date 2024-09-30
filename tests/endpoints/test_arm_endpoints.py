#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

from tests.endpoints.test_core_api_functionality import get_auth_token
from tests.statics import (
                           TEST_USER_PASSWORD,
                           TEST_USER_USERNAME,
                           TEST_ENVIRONMENT_ID,
                           TEST_ARM_ID,
                           INVALID_TOKEN
                           )


@pytest.mark.usefixtures("user", "environment", "arm")
def test_get_arms_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.usefixtures("user", "environment", "arm")
def test_get_arms_unauthenticated(client):
    token = INVALID_TOKEN
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.usefixtures("user", "environment", "arm")
def test_get_arm_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms/{TEST_ARM_ID}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("user", "environment", "arm")
def test_get_arm_unauthenticated(client):
    token = INVALID_TOKEN
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms/{TEST_ARM_ID}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
