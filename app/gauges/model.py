# -*- coding: utf-8 -*-

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, FloatField, HashField
from web3.constants import ADDRESS_ZERO

from app.settings import LOGGER, CACHE, GAUGES_ADDRESS
from app.assets import Token


class Gauge(Model):
    """Gauge model."""
    __database__ = CACHE

    DEFAULT_DECIMALS = 18
    WEEK_IN_SECONDS = 7 * 24 * 60 * 60

    address = TextField(primary_key=True)
    decimals = IntegerField(default=DEFAULT_DECIMALS)
    total_supply = FloatField()
    bribe_address = TextField(index=True)

    # Bribes in the form of `token_address => token_amount`...
    rewards = HashField()

    # TODO: Backwards compat. Remove once no longer needed...
    bribeAddress = TextField()
    totalSupply = FloatField()

    @classmethod
    def find(cls, address):
        """Loads a gauge from cache, of from chain if not found."""
        try:
            return cls.load(address)
        except KeyError:
            return cls.from_chain(address)

    @classmethod
    def from_chain(cls, address):
        """Fetches pair/pool gauge data from chain."""
        pair_gauge_multi = Multicall([
            Call(
                address,
                'totalSupply()(uint256)',
                [['total_supply', None]]
            ),
            Call(
                GAUGES_ADDRESS,
                ['bribes(address)(address)', address],
                [['bribe_address', None]]
            )
        ])

        data = pair_gauge_multi()
        data['decimals'] = cls.DEFAULT_DECIMALS
        data['total_supply'] = data['total_supply'] / data['decimals']

        # TODO: Remove once no longer needed...
        data['bribeAddress'] = data['bribe_address']
        data['totalSupply'] = data['total_supply']

        # Cleanup old data
        try:
            cls.load(address).delete()
        except KeyError:
            pass

        gauge = cls.create(address=address, **data)
        LOGGER.debug('Fetched %s:%s.', cls.__name__, address)

        if data.get('bribe_address') not in (ADDRESS_ZERO, None):
            cls._fetch_rewards(gauge)

        return gauge

    @classmethod
    def _fetch_rewards(cls, gauge):
        """Fetches gauge bribe data from chain."""
        tokens_len = Call(
            gauge.bribe_address,
            'rewardsListLength()(uint256)'
        )()

        for idx in range(0, tokens_len):
            bribe_token_address = Call(
                gauge.bribe_address,
                ['rewards(uint256)(address)', idx]
            )()

            bribe_multi = Multicall([
                Call(
                    gauge.bribe_address,
                    ['rewardRate(address)(uint256)', bribe_token_address],
                    [['reward_rate', None]]
                ),
                Call(
                    GAUGES_ADDRESS,
                    ['isWhitelisted(address)(bool)', bribe_token_address],
                    [['whitelisted', None]]
                )
            ])

            data = bribe_multi()

            if data['whitelisted'] is False:
                continue

            token = Token.find(bribe_token_address)

            reward_rate = data['reward_rate'] / 10**token.decimals
            reward_amount = (
                reward_rate * cls.WEEK_IN_SECONDS / 10**token.decimals
            )

            gauge.rewards[bribe_token_address] = reward_amount

            LOGGER.debug(
                'Fetched %s:%s reward %s:%s.',
                cls.__name__,
                gauge.address,
                bribe_token_address,
                reward_amount
            )

        gauge.save()
