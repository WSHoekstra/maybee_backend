#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request, Response
from sqlmodel import Session
from fastapi_redis_cache import FastApiRedisCache
from maybee_backend.config import Config, get_config


def get_cache(config: Config = get_config()):
    """
    If a Redis cache is configured, initialize and return it. 
    Otherwise, return None.
    """
    if not config.redis_host:
        return None
    
    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=config.redis_host,
        prefix="maybee-backend-cache",
        response_header="X-MaybeeAPI-Cache",
        ignore_arg_types=[Request, Response, Session]
    )
    return redis_cache