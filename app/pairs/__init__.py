# -*- coding: utf-8 -*-

import json
import pickle
from decimal import Decimal

import falcon
from multicall import Call, Multicall
from web3.auto import w3
from web3.constants import ADDRESS_ZERO

from app.assets import Assets
from app.settings import CACHE, LOGGER, FACTORY_ADDRESS, GAUGES_ADDRESS


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for decimals."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


class Pairs(object):
    """Handles our liquidity pools/pairs"""
    # Seconds to expire the cache, ~ the time needed to mine a new block
    EXPIRE_IN = 60

    WEEK_IN_SECONDS = 7 * 24 * 60 * 60

    GAUGE_DECIMALS = 18

    def on_get(self, req, resp):
        """Returns cached liquidity pools/pairs"""
        pairs = CACHE.get('pairs_json')

        if pairs is None:
            pairs = json.dumps(
                dict(data=self.pairs()),
                cls=DecimalEncoder
            )

            CACHE.setex('pairs_json', self.EXPIRE_IN, pairs)
            LOGGER.debug('Cache updated for pairs_json.')

        resp.status = falcon.HTTP_200
        resp.text = pairs

    @classmethod
    def pairs(cls):
        """Fetches and caches liquidity pools/pairs."""
        pairs = CACHE.get(__name__)

        if pairs is not None:
            return pickle.loads(pairs)

        pairs = cls._fetch_pairs()
        CACHE.setex(__name__, cls.EXPIRE_IN, pickle.dumps(pairs))
        LOGGER.debug('Cache updated for %s (%d items).', __name__, len(pairs))

        return pairs

    @classmethod
    def from_wei(cls, value):
        """Converts ether amounts into decimals."""
        return w3.fromWei(value, 'ether')

    @classmethod
    def _fetch_pairs(cls):
        """Fetches pairs/pools from chain."""
        pairs = []

        if w3.isConnected():
            LOGGER.debug('Web3 connection available...')

        pairs_count = Call(FACTORY_ADDRESS, 'allPairsLength()(uint256)')()

        for idx in range(0, pairs_count):
            pair_addr = Call(
                FACTORY_ADDRESS,
                ['allPairs(uint256)(address)', idx]
            )()

            pair = cls._fetch_pair(pair_addr)

            if pair.get('gauge_address') not in (ADDRESS_ZERO, None):
                gauge = cls._fetch_pair_gauge(pair)
                pair['gauge'] = gauge
                pair['bribe_address'] = gauge['bribe_address']
                # TODO: Remove once no longer needed...
                pair['bribeAddress'] = gauge['bribe_address']

            if pair.get('bribe_address') not in (ADDRESS_ZERO, None):
                pair['gauge']['bribes'] = \
                    cls._fetch_gauge_bribes(pair['gauge'])

            pairs.append(pair)

        return pairs

    @classmethod
    def _fetch_pair(cls, address):
        """Fetches pair/pool data from chain."""
        pair_multi = Multicall([
            Call(
                address,
                'getReserves()(uint256,uint256)',
                [['reserve0', None], ['reserve1', None]]
            ),
            Call(address, 'token0()(address)', [['token0_address', None]]),
            Call(address, 'token1()(address)', [['token1_address', None]]),
            Call(
                address,
                'totalSupply()(uint256)',
                [['total_supply', None]]
            ),
            Call(address, 'symbol()(string)', [['symbol', None]]),
            Call(address, 'decimals()(uint8)', [['decimals', None]]),
            Call(address, 'stable()(bool)', [['is_stable', None]]),
            Call(
                GAUGES_ADDRESS,
                ['gauges(address)(address)', address],
                [['gauge_address', None]]
            ),
            Call(
                GAUGES_ADDRESS,
                ['weights(address)(int256)', address],
                [['gauge_weight', cls.from_wei]]
            )
        ])

        data = pair_multi()
        data['address'] = address
        data['token0'] = Assets.token_by_address(data['token0_address'])
        data['token1'] = Assets.token_by_address(data['token1_address'])
        data['total_supply'] = data['total_supply'] / (10**data['decimals'])
        data['reserve0'] = data['reserve0'] / (10**data['decimals'])
        data['reserve1'] = data['reserve1'] / (10**data['decimals'])
        # TODO: Remove once no longer needed...
        data['isStable'] = data['is_stable']
        data['totalSupply'] = data['total_supply']

        return data

    @classmethod
    def _fetch_pair_gauge(cls, pair):
        """Fetches pair/pool gauge data from chain."""
        pair_gauge_multi = Multicall([
            Call(
                pair['gauge_address'],
                'totalSupply()(uint256)',
                [['total_supply', None]]
            ),
            Call(
                GAUGES_ADDRESS,
                ['bribes(address)(address)', pair['gauge_address']],
                [['bribe_address', None]]
            ),
            Call(
                GAUGES_ADDRESS,
                ['totalWeight()(uint256)'],
                [['gauges_total_weight', None]]
            )
        ])

        data = pair_gauge_multi()
        data['decimals'] = cls.GAUGE_DECIMALS
        data['total_supply'] = data['total_supply'] / cls.GAUGE_DECIMALS
        data['weight'] = pair['gauge_weight']

        data['weight_percent'] = 0
        data['reserve0'] = 0
        data['reserve1'] = 0

        if pair['total_supply'] > 0:
            res0 = pair['reserve0'] * data['total_supply']
            res1 = pair['reserve1'] * data['total_supply']
            data['reserve0'] = res0 / pair['total_supply']
            data['reserve1'] = res1 / pair['total_supply']

        if data['gauges_total_weight'] > 0:
            data['weight_percent'] = \
                data['weight'] * 100 / data['gauges_total_weight']

        # TODO: Remove once no longer needed...
        data['weightPercent'] = data['weight_percent']
        data['bribeAddress'] = data['bribe_address']
        data['totalSupply'] = data['total_supply']

        return data

    @classmethod
    def _fetch_gauge_bribes(cls, gauge):
        """Fetches gauge bribe data from chain."""
        bribes = []

        tokens_len = Call(
            gauge['bribe_address'],
            'rewardsListLength()(uint256)'
        )()

        for idx in range(0, tokens_len):
            bribe_token_address = Call(
                gauge['bribe_address'],
                ['rewards(uint256)(address)', idx]
            )()

            gauge_bribe_multi = Multicall([
                Call(
                    gauge['bribe_address'],
                    ['rewardRate(address)(uint256)', bribe_token_address],
                    [['reward_rate', None]]
                ),
                Call(
                    GAUGES_ADDRESS,
                    ['isWhitelisted(address)(bool)', bribe_token_address],
                    [['whitelisted', None]]
                )
            ])

            bribe = gauge_bribe_multi()

            if bribe['whitelisted'] is False:
                continue

            token = Assets.token_by_address(bribe_token_address)

            bribe['token'] = token
            bribe['token_address'] = bribe_token_address
            bribe['reward_rate'] = 0
            bribe['reward_amount'] = bribe['reward_rate'] * cls.WEEK_IN_SECONDS

            if token:
                bribe['reward_rate'] = bribe['reward_rate'] / token['decimals']

            # TODO: Remove once no longer needed...
            bribe['rewardRate'] = bribe['reward_rate']
            bribe['rewardAmount'] = bribe['reward_amount']

            bribes.append(bribe)

        return bribes
