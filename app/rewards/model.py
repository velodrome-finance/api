# -*- coding: utf-8 -*-

from multicall import Call
from walrus import Model, TextField, IntegerField, UUIDField

from app.settings import LOGGER, CACHE, DEFAULT_TOKEN_ADDRESS


class Reward(Model):
    """Generic rewards model."""
    __database__ = CACHE

    pk = UUIDField(primary_key=True)
    token_id = IntegerField(index=True)
    account_address = TextField(index=True)
    token_address = TextField(index=True)
    gauge_address = TextField(index=True)
    pair_address = TextField(index=True)
    amount = TextField()


class EmissionReward(Reward):
    """Emission rewards model."""
    @classmethod
    def prepare_chain_calls(cls, pair, account_address):
        """Returns prepared emission calls for an account."""
        key_name = '|'.join([cls.__name__, pair.address, pair.gauge_address])

        return [
            Call(
                pair.gauge_address,
                [
                    'earned(address,address)(uint256)',
                    DEFAULT_TOKEN_ADDRESS,
                    account_address
                ],
                [[key_name, None]]
            ),
        ]

    @classmethod
    def from_chain_calls(cls, account_address, data):
        """Imports/creates a emission rewards from provided data."""
        rewards = []
        # Cleanup old data...
        cls.query_delete(cls.account_address == account_address.lower())

        if len(data) == 0:
            return []

        for (key_name, amount) in data.items():
            if not key_name.startswith(cls.__name__) or amount == 0:
                continue

            _, pair_addr, gauge_addr = key_name.split('|')

            reward = cls.create(
                token_address=DEFAULT_TOKEN_ADDRESS,
                account_address=account_address.lower(),
                pair_address=pair_addr.lower(),
                gauge_address=gauge_addr.lower(),
                amount=str(amount)
            )

            rewards.append(reward)

        LOGGER.debug(
            'Synced %s %s for %s.', len(rewards), cls.__name__, account_address
        )

        return rewards


class FeeReward(Reward):
    """Fee rewards model."""
    @classmethod
    def prepare_chain_calls(cls, pair, gauge, token_id):
        """Returns prepared gauge-related calls for a token ID emissions."""
        fee0_name = '|'.join(
            [
                cls.__name__,
                str(token_id),
                pair.address,
                pair.gauge_address,
                pair.token0_address
            ]
        )

        fee1_name = '|'.join(
            [
                cls.__name__,
                str(token_id),
                pair.address,
                pair.gauge_address,
                pair.token1_address
            ]
        )

        return [
            Call(
                gauge.fees_address,
                [
                    'earned(address,uint256)(uint256)',
                    pair.token0_address,
                    token_id
                ],
                [[fee0_name, None]]
            ),
            Call(
                gauge.fees_address,
                [
                    'earned(address,uint256)(uint256)',
                    pair.token1_address,
                    token_id
                ],
                [[fee1_name, None]]
            )
        ]

    @classmethod
    def from_chain_calls(cls, account_address, data):
        """Imports/creates a emission rewards from provided data."""
        rewards = []
        # Cleanup old data...
        cls.query_delete(cls.account_address == account_address.lower())

        if len(data) == 0:
            return rewards

        for (key_name, amount) in data.items():
            if not key_name.startswith(cls.__name__) or amount == 0:
                continue

            _, token_id, pair_addr, gauge_addr, token_addr = \
                key_name.split('|')

            reward = cls.create(
                token_id=int(token_id),
                token_address=token_addr.lower(),
                account_address=account_address.lower(),
                pair_address=pair_addr.lower(),
                gauge_address=gauge_addr.lower(),
                amount=str(amount)
            )

            rewards.append(reward)

        LOGGER.debug(
            'Synced %s %s for %s.', len(rewards), cls.__name__, account_address
        )

        return rewards


class BribeReward(FeeReward):
    """Bribe rewards model."""
    @classmethod
    def prepare_chain_calls(cls, pair, gauge, token_id):
        """Returns prepared bribe calls for a token ID."""
        calls = []

        for bribe_token_addr in gauge.rewards.keys():
            key_name = '|'.join(
                [
                    cls.__name__,
                    str(token_id),
                    pair.address,
                    pair.gauge_address,
                    bribe_token_addr.decode('utf-8')
                ]
            )

            calls.append(
                Call(
                    gauge.wrapped_bribe_address,
                    [
                        'earned(address,uint256)(uint256)',
                        bribe_token_addr.decode('utf-8'),
                        token_id
                    ],
                    [[key_name, None]]
                )
            )

        return calls
