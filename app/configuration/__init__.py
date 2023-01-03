# -*- coding: utf-8 -*-

import json

import falcon
from versiontools import Version

from app import __version__
from app.pairs import Token
from app.settings import CACHE, DEFAULT_TOKEN_ADDRESS, STABLE_TOKEN_ADDRESS,\
    ROUTE_TOKEN_ADDRESSES, LOGGER


class Configuration(object):
    """Handles app configuration"""

    CACHE_KEY = 'configuration:json'

    @classmethod
    def recache(cls):
        default_token = Token.find(DEFAULT_TOKEN_ADDRESS)
        stable_token = Token.find(STABLE_TOKEN_ADDRESS)
        route_tokens = [Token.find(token) for token in ROUTE_TOKEN_ADDRESSES]
        route_token_data = [token._data for token in route_tokens]

        conf = json.dumps(
            dict(
                data=[
                    default_token._data,
                    stable_token._data,
                    *route_token_data
                ],
                meta=dict(
                    default_token=default_token._data,
                    stable_token=stable_token._data,
                    version=str(Version(*__version__))
                )
            )
        )

        CACHE.set(cls.CACHE_KEY, conf)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY)

        return conf

    def on_get(self, req, resp):
        """Caches and returns our configuration data"""
        conf = CACHE.get(self.CACHE_KEY) or Configuration.recache()

        resp.text = conf
        resp.status = falcon.HTTP_200
