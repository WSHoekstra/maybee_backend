#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request, Response, Depends
from sqlmodel import Session
from redis import asyncio as redis
from maybee_backend.config import Config, get_config


def get_cache(config: Config = Depends(get_config)) -> redis.Redis:
    """
    If a Redis cache is configured, initialize and return it. 
    Otherwise, return None.
    """
    if not config.redis_host:
        return None
    
    return redis.Redis(host=config.redis_host,
                       port=config.redis_port if config.redis_port else 6379, 
                       db=0,
                       decode_responses=True)


def get_cache_key_for_list_of_all_environments():
    return "environments"

def get_cache_key_for_list_of_all_environments_accessible_to_user(user_id: int):
    return f"environments_for_user:{user_id}"

def get_cache_key_for_environment(environment_id):
    return f"environment:{environment_id}"

def get_cache_key_for_list_of_actions(environment_id):
    return f"actions:{environment_id}"
