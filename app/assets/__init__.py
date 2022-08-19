# -*- coding: utf-8 -*-

import json

import falcon

from app.settings import LOGGER, CACHE
from .model import Token


class Assets(object):
    """Handles our base/chain assets as a tokenlist"""

    CACHE_KEY = 'assets:json'

    @classmethod
    def recache(cls):
        tokens = map(lambda tok: tok._data, Token.all())

        # Remove anything that's not in our token lists...
        tokens = [_t for _t in tokens if _t['logoURI'] is not None]

        assets = json.dumps(dict(data=list(tokens)))

        CACHE.set(cls.CACHE_KEY, assets)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY)

        return assets

    def on_get(self, req, resp):
        """Caches and returns our assets"""
        assets = CACHE.get(self.CACHE_KEY) or Assets.recache()

        resp.status = falcon.HTTP_200
        resp.text = assets
