#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from maybee_backend.models.core_models import Environment, Arm
from maybee_backend.models.user_models import User
from maybee_backend.api.routes import get_password_hash


TEST_USER_USERNAME = "testuser"
TEST_USER_FOR_USER_CREATION_ENDPOINT_TEST_USERNAME = "testuser2"
TEST_ADMIN_USER_USERNAME = "testadmin"

TEST_USER_PASSWORD = "testpassword"
TEST_ENVIRONMENT_ID = 9999
TEST_ARM_ID = 9999

INVALID_TOKEN = "INVALID_TOKEN"

username_field = "username"
password_field = "password"


@pytest.fixture(name="user")
def user_fixture(session: Session):
    user = User(
        username=TEST_USER_USERNAME,
        password_hash=get_password_hash(TEST_USER_PASSWORD),
        is_admin=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    yield user
    session.delete(user)
    session.commit()


@pytest.fixture(name="environment")
def environment_fixture(session: Session):
    environment = Environment(environment_id=TEST_ENVIRONMENT_ID)
    session.add(environment)
    session.commit()
    session.refresh(environment)
    yield environment
    session.delete(environment)
    session.commit()


@pytest.fixture(name="arm")
def arm_fixture(session: Session):
    arm = Arm(
        arm_id=TEST_ARM_ID,
        environment_id=TEST_ENVIRONMENT_ID
    )
    session.add(arm)
    session.commit()
    session.refresh(arm)
    yield arm
    session.delete(arm)
    session.commit()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    user = User(
        username=TEST_ADMIN_USER_USERNAME,
        password_hash=get_password_hash(TEST_USER_PASSWORD),
        is_admin=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    yield user
    session.delete(user)
    session.commit()


# Test health endpoint
def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Test user registration
@pytest.mark.usefixtures("session")
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


@pytest.mark.usefixtures("client", "user")
def test_get_auth_token(client: TestClient):
    response = client.post(
        "/users/token",
        data={username_field: TEST_USER_USERNAME, password_field: TEST_USER_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json().get("access_token") is not None


def get_auth_token(client: TestClient, username: str, password: str):
    response = client.post(
        "/users/token",
        data={username_field: username, password_field: password},
    )
    return response.json()["access_token"]


# Test get environments (authenticated)
@pytest.mark.usefixtures("client", "user")
def test_get_environments_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        "/environments/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Test create environment (as non-admin user)
@pytest.mark.usefixtures("client", "user")
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


# Test create environment (as admin user)
@pytest.mark.usefixtures("client", "admin_user")
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


# Test update environment (as admin user)
@pytest.mark.usefixtures("client", "admin_user", "environment")
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

# Test update environment (as non-admin user)

@pytest.mark.usefixtures("client", "user", "environment")
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


@pytest.mark.usefixtures("client", "user", "environment", "arm")
def test_get_arms_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.usefixtures("client", "user", "environment", "arm")
def test_get_arms_unauthenticated(client):
    token = INVALID_TOKEN
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.usefixtures("client", "user", "environment", "arm")
def test_get_arm_authenticated(client):
    token = get_auth_token(
        client=client, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD
    )
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms/{TEST_ARM_ID}", headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())
    assert response.status_code == 200


@pytest.mark.usefixtures("client", "user", "environment", "arm")
def test_get_arm_unauthenticated(client):
    token = INVALID_TOKEN
    response = client.get(
        f"/environments/{TEST_ENVIRONMENT_ID}/arms/{TEST_ARM_ID}", headers={"Authorization": f"Bearer {token}"}
    )
    print(response.json())
    assert response.status_code == 401