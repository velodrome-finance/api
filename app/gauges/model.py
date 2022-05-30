# -*- coding: utf-8 -*-

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, FloatField, HashField
from web3.constants import ADDRESS_ZERO

from app.settings import LOGGER, CACHE, VOTER_ADDRESS
from app.assets import Token


class Gauge(Model):
    """Gauge model."""
    __database__ = CACHE

    DEFAULT_DECIMALS = 18
    WEEK_IN_SECONDS = 7 * 24 * 60 * 60

    address = TextField(primary_key=True)
    decimals = IntegerField(default=DEFAULT_DECIMALS)
    total_supply = FloatField()
    bribes_address = TextField(index=True)
    fees_address = TextField(index=True)

    # Bribes in the form of `token_address => token_amount`...
    rewards = HashField()

    # TODO: Backwards compat. Remove once no longer needed...
    bribesAddress = TextField()
    feesAddress = TextField()
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
                VOTER_ADDRESS,
                ['external_bribes(address)(address)', address],
                [['bribes_address', None]]
            ),
            Call(
                VOTER_ADDRESS,
                ['internal_bribes(address)(address)', address],
                [['fees_address', None]]
            )
        ])

        data = pair_gauge_multi()
        data['decimals'] = cls.DEFAULT_DECIMALS
        data['total_supply'] = data['total_supply'] / data['decimals']

        # TODO: Remove once no longer needed...
        data['bribesAddress'] = data['bribes_address']
        data['feesAddress'] = data['fees_address']
        data['totalSupply'] = data['total_supply']

        # Cleanup old data
        try:
            cls.load(address).delete()
        except KeyError:
            pass

        gauge = cls.create(address=address, **data)
        LOGGER.debug('Fetched %s:%s.', cls.__name__, address)

        if data.get('bribes_address') not in (ADDRESS_ZERO, None):
            cls._fetch_internal_rewards(gauge)
            cls._fetch_external_rewards(gauge)

        return gauge

    @classmethod
    def _fetch_external_rewards(cls, gauge):
        """Fetches gauge external rewards (bribes) data from chain."""
        tokens_len = Call(
            gauge.bribes_address,
            'rewardsListLength()(uint256)'
        )()

        for idx in range(0, tokens_len):
            bribe_token_address = Call(
                gauge.bribes_address,
                ['rewards(uint256)(address)', idx]
            )()

            bribe_multi = Multicall([
                Call(
                    gauge.bribes_address,
                    [
                        'left(address)(uint256)',
                        bribe_token_address
                    ],
                    [['amount', None]]
                ),
                Call(
                    VOTER_ADDRESS,
                    ['isWhitelisted(address)(bool)', bribe_token_address],
                    [['whitelisted', None]]
                )
            ])

            data = bribe_multi()

            if data['whitelisted'] is False:
                continue

            # Refresh cache if needed...
            token = Token.find(bribe_token_address)

            reward_amount = data['amount'] / 10**18

            gauge.rewards[token.address] = reward_amount

            LOGGER.debug(
                'Fetched %s:%s reward %s:%s.',
                cls.__name__,
                gauge.address,
                bribe_token_address,
                reward_amount
            )

        gauge.save()

    @classmethod
    def _fetch_internal_rewards(cls, gauge):
        """Fetches gauge external rewards (bribes) data from chain."""
        # Avoid circular import...
        from app.pairs.model import Pair

        pair = Pair.get(Pair.gauge_address == gauge.address)

        token0 = Token.find(pair.token0_address)
        token1 = Token.find(pair.token1_address)

        fees = Multicall([
            Call(
                gauge.fees_address,
                ['left(address)(uint256)', pair.token0_address],
                [['fees0', None]]
            ),
            Call(
                gauge.fees_address,
                ['left(address)(uint256)', pair.token1_address],
                [['fees1', None]]
            )
        ])()

        fees0, fees1 = fees['fees0'], fees['fees1']

        if gauge.rewards.get(token0.address):
            gauge.rewards[token0.address] += fees0 / 10**token0.decimals
        else:
            gauge.rewards[token0.address] = fees0 / 10**token0.decimals

        LOGGER.debug(
            'Fetched %s:%s reward %s:%s.',
            cls.__name__,
            gauge.address,
            token0.address,
            gauge.rewards[token0.address]
        )

        if gauge.rewards.get(token1.address):
            gauge.rewards[token1.address] += fees1 / 10**token1.decimals
        else:
            gauge.rewards[token1.address] = fees1 / 10**token1.decimals

        LOGGER.debug(
            'Fetched %s:%s reward %s:%s.',
            cls.__name__,
            gauge.address,
            token1.address,
            gauge.rewards[token0.address]
        )

        gauge.save()
