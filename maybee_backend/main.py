#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from sqlmodel import SQLModel, Session

from maybee_backend.api.routes import router
from maybee_backend.database import get_engine
from maybee_backend.cache import get_cache
from maybee_backend.logging import log, log_level
from maybee_backend.setup.create_admin_user import create_admin_user
from maybee_backend.simulations.simulation_environment import (
    add_simulation_environment,
)

log.info(f"{log_level=}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init db
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    
    # init cache
    cache = get_cache()
    if cache:
        log.info(f"Using redis cache {cache=}")
        app.state.cache = cache
    else:
        log.info("Redis cache not configured.")

    init_admin_username = os.getenv("ADMIN_USERNAME", None)
    init_admin_user_password = os.getenv("ADMIN_PASSWORD", None)
    init_with_admin_user = (
        init_admin_username is not None and init_admin_user_password is not None
    )

    with Session(engine) as session:
        if init_with_admin_user:
            create_admin_user(
                username=init_admin_username,
                password=init_admin_user_password,
                session=session,
            )

        init_with_simulation_environment = os.getenv(
            "INIT_WITH_SIMULATION_ENVIRONMENT", False
        )
        if init_with_simulation_environment:
            add_simulation_environment(session=session, bandit_type="softmax")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
