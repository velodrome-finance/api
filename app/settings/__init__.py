# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import os
import sys

import fakeredis
import redis
import redis.exceptions

# Logger setup...
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(os.getenv('LOGGING_LEVEL', 'DEBUG'))

# Tokenlists are split with a pipe char (unlikely to be used in URIs)
TOKENLISTS = os.getenv('TOKENLISTS', '').split('|')
DEFAULT_TOKEN_ADDRESS = os.getenv('DEFAULT_TOKEN_ADDRESS')
STABLE_TOKEN_ADDRESS = os.getenv('STABLE_TOKEN_ADDRESS')

# Will be picked automatically by web3.py
WEB3_PROVIDER_URI = os.getenv('WEB3_PROVIDER_URI')

FACTORY_ADDRESS = os.getenv('FACTORY_ADDRESS')
GAUGES_ADDRESS = os.getenv('GAUGES_ADDRESS')

# Placeholder for our cache instance (Redis)
CACHE = None

try:
    CACHE = redis.Redis.from_url(os.getenv('REDIS_URL'))
    CACHE.ping()
except (ValueError, redis.exceptions.ConnectionError):
    LOGGER.debug('No Redis server found, using memory ...')
    CACHE = fakeredis.FakeRedis()
