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


class TestingConfig:
    secret_key = "test_secret_key"
    db_uri = "sqlite:///:memory:?check_same_thread=False"


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
