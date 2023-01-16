# -*- coding: utf-8 -*-

import json
from datetime import timedelta

import falcon
from multicall import Call, Multicall

from app.settings import CACHE, DEFAULT_TOKEN_ADDRESS, LOGGER, VE_ADDRESS


class Supply(object):
    """Handles supply info"""

    CACHE_KEY = 'supply:json'
    CACHE_TIME = timedelta(minutes=5)

    @classmethod
    def recache(cls):
        supply_multicall = Multicall([
            Call(
                DEFAULT_TOKEN_ADDRESS,
                'decimals()(uint256)',
                [['token_decimals', None]]
            ),
            Call(
                VE_ADDRESS,
                'decimals()(uint256)',
                [['lock_decimals', None]]
            ),
            Call(
                DEFAULT_TOKEN_ADDRESS,
                'totalSupply()(uint256)',
                [['raw_total_supply', None]]
            ),
            Call(
                DEFAULT_TOKEN_ADDRESS,
                ['balanceOf(address)(uint256)', VE_ADDRESS],
                [['raw_locked_supply', None]]
            ),
        ])

        data = supply_multicall()

        data['total_supply'] = \
            data['raw_total_supply'] / 10**data['token_decimals']
        data['locked_supply'] = \
            data['raw_locked_supply'] / 10**data['lock_decimals']
        data['circulating_supply'] = \
            data['total_supply'] - data['locked_supply']

        supply_data = json.dumps(dict(data=data))

        CACHE.setex(cls.CACHE_KEY, cls.CACHE_TIME, supply_data)
        LOGGER.debug('Cache updated for %s.', cls.CACHE_KEY)

        return supply_data

    def on_get(self, req, resp):
        """Caches and returns our supply info"""
        supply_data = CACHE.get(self.CACHE_KEY) or Supply.recache()

        resp.text = supply_data
        resp.status = falcon.HTTP_200
