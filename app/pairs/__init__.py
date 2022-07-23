# -*- coding: utf-8 -*-

import json
from decimal import Decimal

import falcon

from .model import Pair
from app.assets import Token
from app.gauges import Gauge
from app.settings import CACHE, LOGGER, reset_multicall_pool_executor


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for decimals."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


class Pairs(object):
    """Handles our liquidity pools/pairs"""
    # Seconds to expire the cache, a bit longer than the syncer schedule...

    CACHE_KEY = 'pairs:json'

    @classmethod
    def serialize(cls):
        pairs = []

        for pair in Pair.all():
            data = pair._data
            data['token0'] = Token.find(pair.token0_address)._data
            data['token1'] = Token.find(pair.token1_address)._data

            if pair.gauge_address:
                gauge = Gauge.find(pair.gauge_address)
                data['gauge'] = gauge._data
                data['gauge']['bribes'] = []

                for (token_addr, reward_ammount) in gauge.rewards:
                    data['gauge']['bribes'].append(
                        dict(
                            token=Token.find(token_addr)._data,
                            reward_ammount=float(reward_ammount),
                            # TODO: Backwards compat...
                            rewardAmmount=float(reward_ammount)
                        )
                    )

            pairs.append(data)

        return pairs

    @classmethod
    def recache(cls):
        pairs = json.dumps(
            dict(data=Pairs.serialize()),
            cls=DecimalEncoder
        )

        CACHE.set(cls.CACHE_KEY, pairs)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY)

        return pairs

    def resync(self, pair_address, gauge_address):
        """Resyncs a pair based on it's address or gauge address."""
        if gauge_address:
            old_pair = Pair.get(Pair.gauge_address == gauge_address)
            pair = Pair.from_chain(old_pair.address)
            pair.syncup_gauge()
        elif pair_address:
            pair = Pair.from_chain(pair_address)
            pair.syncup_gauge()
        else:
            return

        reset_multicall_pool_executor()
        Pairs.recache()

    def on_get(self, req, resp):
        """Returns cached liquidity pools/pairs"""
        self.resync(
            req.get_param('pair_address'),
            req.get_param('gauge_address')
        )

        pairs = CACHE.get(self.CACHE_KEY) or Pairs.recache()

        resp.status = falcon.HTTP_200
        resp.text = pairs
