#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pydantic import ValidationError
from maybee_backend.models.core_models import Action


def validate_action_data(data):
    try:
        action_instance = Action(**data)  # Attempt to create an instance
        return True, action_instance
    except ValidationError as e:
        return False, e.errors()
