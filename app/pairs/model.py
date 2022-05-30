# -*- coding: utf-8 -*-

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, BooleanField, FloatField
from web3.constants import ADDRESS_ZERO

from app.settings import LOGGER, CACHE, FACTORY_ADDRESS, VOTER_ADDRESS
from app.gauges import Gauge


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
    bribe_address = TextField(index=True)

    # TODO: Backwards compat. Remove once no longer needed...
    isStable = BooleanField()
    totalSupply = FloatField()

    def syncup_gauge(self):
        """Fetches own gauges data from chain."""
        if self.gauge_address in (ADDRESS_ZERO, None):
            return

        Gauge.from_chain(self.gauge_address)

    @classmethod
    def find(cls, address):
        """Loads a token from cache, of from chain if not found."""
        try:
            return cls.load(address)
        except KeyError:
            return cls.from_chain(address)

    @classmethod
    def chain_syncup(cls):
        """Fetches pairs/pools from chain."""
        pairs_count = Call(FACTORY_ADDRESS, 'allPairsLength()(uint256)')()

        for idx in range(0, pairs_count):
            pair_addr = Call(
                FACTORY_ADDRESS,
                ['allPairs(uint256)(address)', idx]
            )()

            pair = cls.from_chain(pair_addr)
            pair.syncup_gauge()

    @classmethod
    def from_chain(cls, address):
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
                VOTER_ADDRESS,
                ['gauges(address)(address)', address],
                [['gauge_address', None]]
            )
        ])

        data = pair_multi()

        data['address'] = address
        data['total_supply'] = data['total_supply'] / (10**data['decimals'])
        data['reserve0'] = data['reserve0'] / (10**data['decimals'])
        data['reserve1'] = data['reserve1'] / (10**data['decimals'])

        if data.get('gauge_address') in (ADDRESS_ZERO, None):
            data['gauge_address'] = None

        # TODO: Remove once no longer needed...
        data['isStable'] = data['is_stable']
        data['totalSupply'] = data['total_supply']

        # Cleanup old data...
        try:
            cls.load(address).delete()
        except KeyError:
            pass

        pair = cls.create(**data)
        LOGGER.debug('Fetched %s:%s.', cls.__name__, pair.address)

        return pair
