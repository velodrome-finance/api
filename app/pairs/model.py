# -*- coding: utf-8 -*-

import math

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, BooleanField, FloatField
from web3.constants import ADDRESS_ZERO

from app.assets import Token
from app.gauges import Gauge
from app.settings import (
    LOGGER, CACHE, FACTORY_ADDRESS, VOTER_ADDRESS, DEFAULT_TOKEN_ADDRESS
)


class Pair(Model):
    """Liquidity pool pairs model."""
    __database__ = CACHE

    address = TextField(primary_key=True)
    symbol = TextField()
    decimals = IntegerField()
    stable = BooleanField()
    total_supply = FloatField()
    reserve0 = FloatField()
    reserve1 = FloatField()
    token0_address = TextField(index=True)
    token1_address = TextField(index=True)
    gauge_address = TextField(index=True)
    tvl = FloatField(default=0)
    apr = FloatField(default=0)

    # TODO: Backwards compat. Remove once no longer needed...
    isStable = BooleanField()
    totalSupply = FloatField()

    def token_price(self):
        """LP token price.

        Uses: https://blog.alphaventuredao.io/fair-lp-token-pricing/
        """
        token0_price = Token.find(self.token0).chain_price_in_stables()
        token1_price = Token.find(self.token1).chain_price_in_stables()

        if token0_price == 0 or token1_price == 0:
            return 0

        sqrtK = math.sqrt(self.reserve0 * self.reserve1)
        sqrtP = math.sqrt(token0_price * token1_price)

        return 2 * ((sqrtK * sqrtP) / self.totalSupply)

    def syncup_gauge(self):
        """Fetches own gauges data from chain."""
        if self.gauge_address in (ADDRESS_ZERO, None):
            return

        gauge = Gauge.from_chain(self.gauge_address)
        self._update_apr(gauge)

        return gauge

    def _update_apr(self, gauge):
        """Calculates the pool TVL"""
        if self.tvl == 0:
            return

        token = Token.find(DEFAULT_TOKEN_ADDRESS)
        token_price = token.chain_price_in_stables()

        daily_apr = (gauge.reward * token_price) / self.tvl * 100

        self.apr = daily_apr * 365
        self.save()

    @classmethod
    def find(cls, address):
        """Loads a token from cache, of from chain if not found."""
        if address is None:
            return None

        try:
            return cls.load(address.lower())
        except KeyError:
            return cls.from_chain(address.lower())

    @classmethod
    def chain_addresses(cls):
        """Fetches pairs/pools from chain."""
        pairs_count = Call(FACTORY_ADDRESS, 'allPairsLength()(uint256)')()

        pairs_multi = Multicall([
            Call(
                FACTORY_ADDRESS,
                ['allPairs(uint256)(address)', idx],
                [[idx, None]]
            )
            for idx in range(0, pairs_count)
        ])

        return list(pairs_multi().values())

    @classmethod
    def from_chain(cls, address):
        """Fetches pair/pool data from chain."""
        address = address.lower()

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
            Call(address, 'stable()(bool)', [['stable', None]]),
            Call(
                VOTER_ADDRESS,
                ['gauges(address)(address)', address],
                [['gauge_address', None]]
            )
        ])

        data = pair_multi()

        data['address'] = address
        data['total_supply'] = data['total_supply'] / (10**data['decimals'])

        token0 = Token.find(data['token0_address'])
        token1 = Token.find(data['token1_address'])

        data['reserve0'] = data['reserve0'] / (10**token0.decimals)
        data['reserve1'] = data['reserve1'] / (10**token1.decimals)

        if data.get('gauge_address') in (ADDRESS_ZERO, None):
            data['gauge_address'] = None
        else:
            data['gauge_address'] = data['gauge_address'].lower()

        data['tvl'] = cls._tvl(data, token0, token1)

        # TODO: Remove once no longer needed...
        data['isStable'] = data['stable']
        data['totalSupply'] = data['total_supply']

        # Cleanup old data...
        cls.query_delete(cls.address == address.lower())

        pair = cls.create(**data)
        LOGGER.debug('Fetched %s:%s.', cls.__name__, pair.address)

        pair.syncup_gauge()

        return pair

    @classmethod
    def _tvl(cls, pool_data, token0, token1):
        """Returns the TVL of the pool."""
        token0_price = token0.aggregated_price_in_stables()
        token1_price = token1.aggregated_price_in_stables()

        tvl = 0

        if token0_price != 0:
            tvl += pool_data['reserve0'] * token0_price

        if token1_price != 0:
            tvl += pool_data['reserve1'] * token1_price

        return tvl
