# -*- coding: utf-8 -*-

import json

import falcon
from versiontools import Version

from app import __version__
from app.pairs import Pair, Token
from app.settings import CACHE, DEFAULT_TOKEN_ADDRESS, STABLE_TOKEN_ADDRESS,\
    ROUTE_TOKEN_ADDRESSES


class Configuration(object):
    """Returns a app configuration object"""

    def on_get(self, req, resp):
        default_token = Token.find(DEFAULT_TOKEN_ADDRESS)
        stable_token = Token.find(STABLE_TOKEN_ADDRESS)
        route_tokens = [Token.find(token) for token in ROUTE_TOKEN_ADDRESSES]
        route_token_data = [token._data for token in route_tokens]
        tvl = sum(map(lambda p: (p.tvl or 0), Pair.all()))
        max_apr = max(map(lambda p: (p.apr or 0), Pair.all()))

        resp.status = falcon.HTTP_200
        resp.text = json.dumps(
            dict(
                data=[
                    default_token._data,
                    stable_token._data,
                    *route_token_data
                ],
                meta=dict(
                    tvl=tvl,
                    max_apr=max_apr,
                    default_token=default_token._data,
                    stable_token=stable_token._data,
                    cache=(CACHE.connection is not None),
                    version=str(Version(*__version__))
                )
            )
        )
