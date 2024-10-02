#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.engine import Engine
from maybee_backend.main import app
from fastapi.testclient import TestClient
from maybee_backend.config import get_config
from maybee_backend.database import get_session
from sqlmodel.pool import StaticPool
from maybee_backend.api.routes import get_password_hash
from maybee_backend.models.core_models import Action, Environment, Arm, AvgRewardsPerArm, BanditState
from maybee_backend.models.user_models import User, UserEnvironmentLink
from tests.statics import (TEST_USER_ID, TEST_USER_USERNAME, TEST_USER_PASSWORD, TEST_ARM_ID, TEST_ENVIRONMENT_ID, TEST_ADMIN_USER_USERNAME, TEST_ADMIN_USER_ID)


class TestingConfig:
    secret_key = "test_secret_key"
    db_uri = "sqlite:///:memory:?check_same_thread=False"
    redis_host = None


def get_test_config():
    return TestingConfig()


def get_test_engine():
    return create_engine(TestingConfig().db_uri)


def get_test_session(engine: Engine):
    return Session(engine)


@pytest.fixture(autouse=True)
def override_config(monkeypatch):
    monkeypatch.setattr("maybee_backend.config.Config", TestingConfig)


@pytest.fixture(autouse=True)
def override_get_config(monkeypatch):
    monkeypatch.setattr("maybee_backend.config.get_config", get_test_config)


@pytest.fixture(autouse=True)
def override_get_engine(monkeypatch):
    monkeypatch.setattr("maybee_backend.database.get_engine", get_test_engine)


@pytest.fixture(autouse=True)
def override_get_session(monkeypatch):
    monkeypatch.setattr("maybee_backend.database.get_session", get_test_session)


@pytest.fixture(name="session", scope="function", autouse=True)
def session_fixture():
    config = TestingConfig()
    engine = create_engine(
        config.db_uri, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client", autouse=True)
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_config] = get_test_config

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()



@pytest.fixture(name="user")
def user_fixture(session: Session):
    user = User(
        user_id=TEST_USER_ID,
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


@pytest.fixture(name="userenvironmentlink")
def user_environment_link_fixture(session: Session):
    user_environment_link = UserEnvironmentLink(environment_id=TEST_ENVIRONMENT_ID, user_id=TEST_USER_ID)
    session.add(user_environment_link)
    session.commit()
    session.refresh(user_environment_link)
    yield user_environment_link
    session.delete(user_environment_link)
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


@pytest.fixture(name="avgrewardsperarm")
def avg_rewards_per_arm_fixture(session: Session):
    avg_rewards_per_arm = AvgRewardsPerArm(
        arm_id=TEST_ARM_ID,
        environment_id=TEST_ENVIRONMENT_ID,
        n_observations=1,
        avg_reward=1.0,
    )
    session.add(avg_rewards_per_arm)
    session.commit()
    session.refresh(avg_rewards_per_arm)
    yield avg_rewards_per_arm
    session.delete(avg_rewards_per_arm)
    session.commit()


@pytest.fixture(name="action")
def action_fixture(session: Session):
    action = Action(arm_id=TEST_ARM_ID,
            environment_id=TEST_ENVIRONMENT_ID,
            bandit_state=BanditState.EXPLORE.value,
    )
    session.add(action)
    session.commit()
    session.refresh(action)
    yield action
    session.delete(action)
    session.commit()


@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    user = User(
        user_id=TEST_ADMIN_USER_ID,
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