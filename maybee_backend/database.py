#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Depends
import os
from sqlmodel import create_engine, Session
from sqlalchemy.engine import Engine


def get_engine() -> Engine:
    return create_engine(os.getenv("DB_URI", None))


def get_session(engine: Engine = Depends(get_engine)) -> Session:
    with Session(engine) as session:
        return session
