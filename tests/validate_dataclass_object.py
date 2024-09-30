#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pydantic import ValidationError
from sqlmodel import SQLModel
from enum import Enum


class Plurality(Enum):
    SINGULAR = "singular"
    PLURAL = "plural"


def validate_dataclass_object(data: dict, dataclass: SQLModel, plurality: Plurality = Plurality.SINGULAR):
    if plurality == Plurality.SINGULAR:
        try:
            dataclass_instance = dataclass(**data)  # Attempt to create an instance
            return True, dataclass_instance
        except ValidationError as e:
            return False, e.errors()
    else: # plural
        try:
            dataclass_instances = [dataclass(**element) for element in data]
            return True, dataclass_instances
        except ValidationError as e:
            return False, e.errors()
