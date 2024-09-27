#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Dict, List
import logging

import requests
from maybee_backend.models.core_models import (Action, Arm, AvgRewardsPerArm,
                                               Environment, Observation)


default_host = "http://localhost:80"


class MaybeeClient():
    """
    Client for the Maybee API
    """
    def __init__(self, username, password, host=default_host) -> None:
        if host == default_host:
            logging.info("Initializing Maybee client for localhost")
        self.host = host
        self.username = username
        self.password = password
        self._access_token = None
        
        
    def _get_fresh_access_token(self) -> str:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"username": self.username,
                "password": self.password}
        r = requests.post(url=f"{self.host}/users/token", data=data, headers=headers)
        r.raise_for_status()
        token = r.json().get("access_token", None)
        if not token:
            raise Exception(f"Failed to retrieve access token from {self.host}")
        return token
    

    @property
    def access_token(self) -> str:
        """
        Get an access token and cache it for future requests.
        """
        if not self._access_token:
            self._access_token = self._get_fresh_access_token()
        return self._access_token


    def _get_headers_for_authorized_request(self) -> Dict:
        return {"Authorization": f"Bearer {self.access_token}", 
                "Content-Type": "application/json"}
    

    def get_environments(self) -> List[Environment]:
        r = requests.get(
            url=f"{self.host}/environments", 
            headers=self._get_headers_for_authorized_request()
            )
        r.raise_for_status()
        return [Environment.model_validate(entry) for entry in r.json()]


    def get_arms(self, environment_id) -> List[Arm]:
        r = requests.get(
            url=f"{self.host}/environments/{environment_id}/arms", 
            headers=self._get_headers_for_authorized_request()
            )
        r.raise_for_status()
        return [Arm.model_validate(entry) for entry in r.json()]
    
    
    def get_actions(self, environment_id) -> List[Action]:
        r = requests.get(
            url=f"{self.host}/environments/{environment_id}/actions", 
            headers=self._get_headers_for_authorized_request()
            )
        r.raise_for_status()
        return [Action.model_validate(entry) for entry in r.json()]
    

    def get_observations(self, environment_id) -> List[Observation]:
        r = requests.get(
            url=f"{self.host}/environments/{environment_id}/arms", 
            headers=self._get_headers_for_authorized_request()
            )
        r.raise_for_status()
        return [Observation.model_validate(entry) for entry in r.json()]
    

    def get_avg_rewards_per_arm(self, environment_id) -> List[AvgRewardsPerArm]:
        r = requests.get(
            url=f"{self.host}/environments/{environment_id}/arms/average_rewards", 
            headers=self._get_headers_for_authorized_request()
            )
        r.raise_for_status()
        return [AvgRewardsPerArm.model_validate(entry) for entry in r.json()]



        
