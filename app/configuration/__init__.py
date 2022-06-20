# -*- coding: utf-8 -*-

import json

import falcon
from versiontools import Version

from app import __version__
from app.pairs import Pair, Token
from app.settings import CACHE, DEFAULT_TOKEN_ADDRESS, STABLE_TOKEN_ADDRESS, WETH_TOKEN_ADDRESS


class Configuration(object):
    """Returns a app configuration object"""

    def on_get(self, req, resp):
        default_token = Token.find(DEFAULT_TOKEN_ADDRESS)
        stable_token = Token.find(STABLE_TOKEN_ADDRESS)
        weth_token = Token.find(WETH_TOKEN_ADDRESS)
        tvl = sum(map(lambda p: p.tvl, Pair.all()))
        max_apr = max(map(lambda p: p.apr, Pair.all()))

        resp.status = falcon.HTTP_200
        resp.text = json.dumps(
            dict(
                data=[default_token._data, stable_token._data, weth_token._data],
                meta=dict(
                    tvl=tvl,
                    max_apr=max_apr,
                    default_token=default_token._data,
                    stable_token=stable_token._data,
                    weth_token=weth_token._data,
                    cache=(CACHE.connection is not None),
                    version=str(Version(*__version__))
                )
            )
        )
