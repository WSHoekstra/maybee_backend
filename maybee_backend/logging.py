#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import logging
from loguru import logger

# disable logging module logger
logger.remove()
logging.root.handlers = []

# enable loguru module logger
log_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
logger.add(
    sys.stderr,
    level=log_level,
    format="{time} {level} {message}",
    backtrace=True,
    diagnose=True,
)

log = logger
