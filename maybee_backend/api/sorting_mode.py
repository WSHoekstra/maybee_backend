#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum


class SortingMode(str, Enum):
    LATEST = "latest"
    EARLIEST = "earliest"
