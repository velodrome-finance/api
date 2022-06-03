# -*- coding: utf-8 -*-
from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, FloatField, HashField
from web3.constants import ADDRESS_ZERO

from app.settings import LOGGER, CACHE, VOTER_ADDRESS, DEFAULT_TOKEN_ADDRESS
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
    fees_address = TextField(index=True)
    # Per epoch...
    reward = FloatField()

    # Bribes in the form of `token_address => token_amount`...
    rewards = HashField()

    # TODO: Backwards compat. Remove once no longer needed...
    bribeAddress = TextField()
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
                address,
                ['left(address)(uint256)', DEFAULT_TOKEN_ADDRESS],
                [['reward', None]]
            ),
            Call(
                VOTER_ADDRESS,
                ['external_bribes(address)(address)', address],
                [['bribe_address', None]]
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

        token = Token.find(DEFAULT_TOKEN_ADDRESS)
        data['reward'] = data['reward'] / 10**token.decimals

        # TODO: Remove once no longer needed...
        data['bribeAddress'] = data['bribe_address']
        data['feesAddress'] = data['fees_address']
        data['totalSupply'] = data['total_supply']

        # Cleanup old data
        try:
            cls.load(address).delete()
        except KeyError:
            pass

        gauge = cls.create(address=address, **data)
        LOGGER.debug('Fetched %s:%s.', cls.__name__, address)

        if data.get('bribe_address') not in (ADDRESS_ZERO, None):
            cls._fetch_external_rewards(gauge)
            cls._fetch_internal_rewards(gauge)

        return gauge

    @classmethod
    def _fetch_external_rewards(cls, gauge):
        """Fetches gauge external rewards (bribes) data from chain."""
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

            if data['amount'] == 0:
                continue

            # Refresh cache if needed...
            token = Token.find(bribe_token_address)

            gauge.rewards[token.address] = data['amount'] / 10**token.decimals

            LOGGER.debug(
                'Fetched %s:%s reward %s:%s.',
                cls.__name__,
                gauge.address,
                bribe_token_address,
                gauge.rewards[token.address]
            )

        gauge.save()

    @classmethod
    def _fetch_internal_rewards(cls, gauge):
        """Fetches gauge internal rewards (fees) data from chain."""
        # Avoid circular import...
        from app.pairs.model import Pair

        pair = Pair.get(Pair.gauge_address == gauge.address)

        fees_data = Multicall([
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

        fees = [
            [pair.token0_address, fees_data['fees0']],
            [pair.token1_address, fees_data['fees1']]
        ]

        for (token_address, fee) in fees:
            token = Token.find(token_address)

            if gauge.rewards.get(token_address) and fee > 0:
                gauge.rewards[token_address] = (
                    float(gauge.rewards[token_address]) + (
                        fee / 10**token.decimals
                    )
                )
            elif fee > 0:
                gauge.rewards[token_address] = fee / 10**token.decimals

            if fee > 0:
                LOGGER.debug(
                    'Fetched %s:%s reward %s:%s.',
                    cls.__name__,
                    gauge.address,
                    token_address,
                    gauge.rewards[token_address]
                )
            else:
                LOGGER.debug(
                    'Fetched %s:%s and skipped zero reward for %s.',
                    cls.__name__,
                    gauge.address,
                    token_address
                )

        gauge.save()
