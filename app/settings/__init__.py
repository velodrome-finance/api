# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import os
import sys

import fakeredis
import redis.exceptions
from walrus import Database

# Logger setup...
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(os.getenv('LOGGING_LEVEL', 'DEBUG'))

# Tokenlists are split with a pipe char (unlikely to be used in URIs)
TOKENLISTS = os.getenv('TOKENLISTS', '').split('|')
DEFAULT_TOKEN_ADDRESS = os.getenv('DEFAULT_TOKEN_ADDRESS').lower()
STABLE_TOKEN_ADDRESS = os.getenv('STABLE_TOKEN_ADDRESS').lower()
ROUTE_TOKEN_ADDRESSES = \
    os.getenv('ROUTE_TOKEN_ADDRESSES', '').lower().split(',')
# Will be picked automatically by web3.py
WEB3_PROVIDER_URI = os.getenv('WEB3_PROVIDER_URI')

FACTORY_ADDRESS = os.getenv('FACTORY_ADDRESS')
VOTER_ADDRESS = os.getenv('VOTER_ADDRESS')
ROUTER_ADDRESS = os.getenv('ROUTER_ADDRESS')

# Seconds to wait before running the chain syncup. `0` disables it!
SYNC_WAIT_SECONDS = int(os.getenv('SYNC_WAIT_SECONDS', 0))

# Placeholder for our cache instance (Redis)
CACHE = None

try:
    CACHE = Database.from_url(os.getenv('REDIS_URL'))
    CACHE.ping()
except (ValueError, redis.exceptions.ConnectionError):
    LOGGER.debug('No Redis server found, using memory ...')
    # Patch walrus duh...
    # See: https://github.com/coleifer/walrus/issues/95
    db_class = Database
    db_class.__bases__ = (fakeredis.FakeRedis,)
    CACHE = db_class()
