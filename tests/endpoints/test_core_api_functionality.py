#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient

from tests.statics import (
    username_field,
    password_field, 
    TEST_USER_FOR_USER_CREATION_ENDPOINT_TEST_USERNAME, 
    TEST_USER_PASSWORD,
    TEST_USER_USERNAME,
    )


def get_auth_token(client: TestClient, username: str, password: str):
    response = client.post(
        "/users/token",
        data={username_field: username, password_field: password},
    )
    return response.json()["access_token"]


# Test health endpoint -> should suceed
def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Test user registration -> should succeed
def test_create_user(client: TestClient):
    response = client.post(
        "/users/register/",
        json={
            username_field: TEST_USER_FOR_USER_CREATION_ENDPOINT_TEST_USERNAME,
            password_field: TEST_USER_PASSWORD,
        },
    )
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"
    assert (
        "user_id" in response.json()
    ), f"Expected 'user_id' in response, but got: {response.json()}"
    assert (
        response.json()[username_field]
        == TEST_USER_FOR_USER_CREATION_ENDPOINT_TEST_USERNAME
    ), f"Expected username '{TEST_USER_FOR_USER_CREATION_ENDPOINT_TEST_USERNAME}', but got: {response.json().get(username_field)}"


# Test getting an auth token -> should succeed
@pytest.mark.usefixtures("user")
def test_get_auth_token(client: TestClient):
    response = client.post(
        "/users/token",
        data={username_field: TEST_USER_USERNAME, password_field: TEST_USER_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json().get("access_token") is not None
