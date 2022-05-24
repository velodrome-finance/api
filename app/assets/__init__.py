# -*- coding: utf-8 -*-

import json
import pickle

import falcon
import requests

from app.settings import CACHE, LOGGER, TOKENLISTS


class Assets(object):
    """Handles our base/chain assets as a tokenlist"""

    # Seconds to expire the cache
    EXPIRE_IN = 60 * 60

    def on_get(self, req, resp):
        """Caches and returns our assets"""
        assets = CACHE.get('assets_json')

        if assets is None:
            tokens = self.tokens()

            assets = json.dumps(dict(data=tokens))

            CACHE.setex('assets_json', self.EXPIRE_IN, assets)
            LOGGER.debug('Cache updated for assets_json.')

        resp.status = falcon.HTTP_200
        resp.text = assets

    @classmethod
    def tokens(cls):
        """Caches and returns the cached list of tokens."""
        tokens = CACHE.get(__name__)

        if tokens is not None:
            return pickle.loads(tokens)

        tokens = cls._fetch_tokenlists()
        CACHE.setex(__name__, cls.EXPIRE_IN, pickle.dumps(tokens))
        LOGGER.debug('Cache updated for %s (%d items).', __name__, len(tokens))

        return tokens

    @classmethod
    def token_by_address(cls, address):
        """Caches and returns the token by address."""
        key = 'token:%s' % address
        token = CACHE.get(key)

        if type(address) is not str:
            return None

        if token is not None:
            return pickle.loads(token)

        for ftoken in cls.tokens():
            if ftoken['address'].lower() == address.lower():
                token = ftoken
                break

        CACHE.setex(key, cls.EXPIRE_IN, pickle.dumps(token))
        LOGGER.debug('Cache updated for %s.', key)

        return token

    @classmethod
    def _fetch_tokenlists(cls):
        """Fetches and merges all the tokens from available tokenlists."""
        tokens = []

        for tlist in TOKENLISTS:
            try:
                tres = requests.get(tlist).json()
                tokens += tres['tokens']
            except Exception as error:
                LOGGER.error(error)
                continue

        return tokens
