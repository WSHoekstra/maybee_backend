#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os


class Config:
    print("Creating config")
    db_uri = os.getenv("DB_URI", None)
    secret_key = os.getenv("SECRET_KEY", None)
    redis_host = os.getenv("REDIS_HOST", None)


def get_config():
    return Config()
