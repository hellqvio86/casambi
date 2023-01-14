#!/usr/bin/python3
"""
Library for Casambi Cloud api.
Request api_key at: https://developer.casambi.com/
"""
import logging


_LOGGER = logging.getLogger(__name__)


class CasambiApiException(Exception):
    """Custom exception"""


class ConfigException(Exception):
    """Custom exception"""
