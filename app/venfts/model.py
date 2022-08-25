# -*- coding: utf-8 -*-

from datetime import datetime

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, DateTimeField

from app.rewards import BribeReward, EmissionReward, FeeReward
from app.pairs import Gauge, Pair
from app.settings import (
    LOGGER, CACHE, VE_ADDRESS, VOTER_ADDRESS, REWARDS_DIST_ADDRESS
)


class NullableDateTimeField(DateTimeField):
    """Patched datetime field to support null values."""
    def python_value(self, value):
        if not value or float(value) == 0:
            return None

        return super(NullableDateTimeField, self).python_value(value)


class VeNFT(Model):
    """veNFT model."""
    __database__ = CACHE

    token_id = IntegerField(primary_key=True)
    account_address = TextField(index=True)
    decimals = IntegerField(default=0)
    amount = TextField()
    voting_amount = TextField()
    rebase_amount = TextField()
    lock_ends_at = NullableDateTimeField(default=None)
    voted_at = NullableDateTimeField(default=None)

    @classmethod
    def from_chain(cls, address):
        """Fetches on-chain veNFT data for an account address."""
        address = address.lower()
        token_ids = cls._fetch_token_ids(address)
        venfts = []

        if len(token_ids) == 0:
            return venfts

        calls = []
        fee_calls = []
        bribe_calls = []

        for token_id in token_ids:
            calls.extend(cls.prepare_chain_calls(token_id))

        for gauge in Gauge.all():
            pair = Pair.get(Pair.gauge_address == gauge.address)

            calls.extend(EmissionReward.prepare_chain_calls(pair, address))

            for token_id in token_ids:
                fee_calls.extend(
                    FeeReward.prepare_chain_calls(pair, gauge, token_id)
                )
                bribe_calls.extend(
                    BribeReward.prepare_chain_calls(pair, gauge, token_id)
                )

        t0 = datetime.utcnow()
        multi_data = Multicall(calls)()
        multi_fees = Multicall(fee_calls)()
        multi_bribes = Multicall(bribe_calls)()
        tdelta = datetime.utcnow() - t0

        LOGGER.debug(
            'Fetched data for %s %ss in %s.',
            len(token_ids),
            cls.__name__,
            tdelta
        )

        for token_id in token_ids:
            token_prefix = '|'.join([cls.__name__, str(token_id), ''])
            vdata = {
                k.removeprefix(token_prefix): v
                for (k, v) in multi_data.items() if token_prefix in k
            }

            venfts.append(cls.from_chain_calls(address, token_id, vdata))

        EmissionReward.from_chain_calls(address, multi_data)
        FeeReward.from_chain_calls(address, multi_fees)
        BribeReward.from_chain_calls(address, multi_bribes)

        return venfts

    @classmethod
    def prepare_chain_calls(cls, token_id):
        """Returns prepared vote-escrow and voter calls for a token ID."""
        key_prefix = '|'.join([cls.__name__, str(token_id)])

        return [
            Call(
                VE_ADDRESS,
                ['decimals()(uint256)'],
                [['%s|decimals' % key_prefix, None]]
            ),
            Call(
                VE_ADDRESS,
                ['balanceOfNFT(uint256)(uint256)', token_id],
                [['%s|voting_amount' % key_prefix, str]]
            ),
            Call(
                VE_ADDRESS,
                ['locked(uint256)(int128,uint256)', token_id],
                [
                    ['%s|amount' % key_prefix, str],
                    ['%s|lock_ends_at' % key_prefix, None]
                ]
            ),
            Call(
                VOTER_ADDRESS,
                ['lastVoted(uint256)(uint256)', token_id],
                [['%s|voted_at' % key_prefix, None]]
            ),
            Call(
                REWARDS_DIST_ADDRESS,
                ['claimable(uint256)(uint256)', token_id],
                [['%s|rebase_amount' % key_prefix, str]]
            )
        ]

    @classmethod
    def from_chain_calls(cls, account_address, token_id, data):
        """Imports/creates a veNFT from provided data."""
        # Cleanup old data...
        cls.query_delete(cls.token_id == token_id)

        data['token_id'] = token_id
        data['account_address'] = account_address.lower()

        if data['voted_at'] != 0:
            data['voted_at'] = datetime.utcfromtimestamp(data['voted_at'])
        else:
            data['voted_at'] = None

        if data['lock_ends_at'] != 0:
            data['lock_ends_at'] = \
                datetime.utcfromtimestamp(data['lock_ends_at'])
        else:
            data['lock_ends_at'] = None

        venft = cls.create(**data)

        LOGGER.debug('Synced %s:%s.', cls.__name__, token_id)

        return venft

    @classmethod
    def _fetch_token_ids(cls, address):
        """Returns account address veNFT ids."""
        tokens_count = Call(
            VE_ADDRESS, ['balanceOf(address)(uint256)', address]
        )()

        if tokens_count == 0:
            return []

        calls = []

        for idx in range(0, tokens_count):
            call = Call(
                VE_ADDRESS,
                [
                    'tokenOfOwnerByIndex(address,uint256)(uint256)',
                    address, idx
                ],
                [['venft_idx_%s' % idx, None]]
            )
            calls.append(call)

        return list(Multicall(calls)().values())
