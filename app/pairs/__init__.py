# -*- coding: utf-8 -*-

import json
from decimal import Decimal

import falcon

from .model import Pair
from app.assets import Token
from app.gauges import Gauge
from app.settings import CACHE, LOGGER


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

    def serialize(self):
        pairs = []

        for pair in Pair.all():
            data = pair._data
            data['gauge'] = {}

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

    def resync(self, pair_address, gauge_address):
        if pair_address:
            pair = Pair.from_chain(pair_address)
        elif gauge_address:
            gauge = Gauge.from_chain(gauge_address)
            pair = Pair.get(Pair.gauge_address == gauge.address)
            if pair:
                Pair.from_chain(pair.address)
        else:
            return

        CACHE.delete(self.CACHE_KEY)

    def on_get(self, req, resp):
        """Returns cached liquidity pools/pairs"""
        self.resync(
            req.get_param('pair_address'),
            req.get_param('gauge_address')
        )

        pairs = CACHE.get(self.CACHE_KEY)

        if pairs is None:
            pairs = json.dumps(
                dict(data=self.serialize()),
                cls=DecimalEncoder
            )

            CACHE.set(self.CACHE_KEY, pairs)
            LOGGER.debug('Cache updated for pairs:json.')

        resp.status = falcon.HTTP_200
        resp.text = pairs
