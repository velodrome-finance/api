# -*- coding: utf-8 -*-

import json

import falcon
from web3 import Web3

from .model import VeNFT
from app.misc import JSONEncoder
from app.settings import CACHE, LOGGER, reset_multicall_pool_executor


class Accounts(object):
    """Handles our account veNFTs."""
    KEEPALIVE = 60 * 30
    CACHE_KEY = 'account:%s:json'

    @classmethod
    def recache(cls, address):
        venfts = VeNFT.from_chain(address)

        data = list(map(lambda nft: nft._data, venfts))

        serialized = json.dumps(dict(data=data), cls=JSONEncoder)

        CACHE.setex(cls.CACHE_KEY % address, cls.KEEPALIVE, serialized)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY % address)

        reset_multicall_pool_executor()

        return serialized

    def on_get(self, req, resp):
        """Returns cached liquidity pools/pairs"""
        address = req.get_param('address')
        refresh = req.get_param('refresh')

        resp.status = falcon.HTTP_200

        if not Web3.isAddress(address):
            resp.text = json.dumps(dict(data=[]))
            return

        if refresh:
            data = Accounts.recache(address)
        else:
            cache_key = self.CACHE_KEY % address
            data = CACHE.get(cache_key) or Accounts.recache(address)

        resp.text = data
