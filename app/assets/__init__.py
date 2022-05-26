# -*- coding: utf-8 -*-

import json

import falcon

from app.settings import LOGGER, CACHE
from .model import Token


class Assets(object):
    """Handles our base/chain assets as a tokenlist"""

    # Seconds to expire the cache
    EXPIRE_IN = 60 * 60

    def on_get(self, req, resp):
        """Caches and returns our assets"""
        assets = CACHE.get('assets:json')

        if assets is None:
            tokens = map(lambda tok: tok._data, Token.all())

            assets = json.dumps(dict(data=list(tokens)))

            CACHE.setex('assets:json', self.EXPIRE_IN, assets)
            LOGGER.debug('Cache updated for assets:json.')

        resp.status = falcon.HTTP_200
        resp.text = assets
