# -*- coding: utf-8 -*-

import json

import falcon
from web3 import Web3

from .model import VeNFT
from app.pairs import Gauge, Pair, Token
from app.rewards import BribeReward, EmissionReward, FeeReward
from app.misc import JSONEncoder
from app.settings import CACHE, LOGGER, reset_multicall_pool_executor


class Accounts(object):
    """Handles our account veNFTs."""
    KEEPALIVE = 60 * 30
    CACHE_KEY = 'account:%s:json'

    @classmethod
    def serialize(cls, address):
        serialized = []
        venfts = VeNFT.from_chain(address)

        reset_multicall_pool_executor()

        for venft in venfts:
            data = venft._data
            data['rewards'] = []

            rewards = list(
                BribeReward.query(BribeReward.account_address == address)
            )
            rewards.extend(
                list(FeeReward.query(FeeReward.account_address == address))
            )
            rewards.extend(
                list(
                    EmissionReward.query(
                        EmissionReward.account_address == address
                    )
                )
            )

            for reward in rewards:
                rdata = reward._data

                rdata['source'] = \
                    reward.__class__.__name__.replace('Reward', '')

                if reward.token_address:
                    rdata['token'] = Token.find(reward.token_address)._data

                if reward.pair_address:
                    rdata['pair'] = Pair.find(reward.pair_address)._data

                if reward.gauge_address:
                    rdata['gauge'] = Gauge.find(reward.gauge_address)._data

                data['rewards'].append(rdata)

            serialized.append(data)

        return serialized

    @classmethod
    def recache(cls, address):
        serialized = json.dumps(
            dict(data=cls.serialize(address)), cls=JSONEncoder
        )

        CACHE.setex(cls.CACHE_KEY % address, cls.KEEPALIVE, serialized)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY % address)

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
