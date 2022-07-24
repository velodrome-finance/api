# -*- coding: utf-8 -*-

from datetime import datetime

from multicall import Call, Multicall
from walrus import Model, TextField, IntegerField, FloatField, DateTimeField

from app.settings import LOGGER, CACHE, VE_ADDRESS, VOTER_ADDRESS


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
    amount = FloatField(default=0)
    voting_amount = FloatField(default=0)
    lock_ends_at = NullableDateTimeField(default=None)
    voted_at = NullableDateTimeField(default=None)

    @classmethod
    def from_chain(cls, address):
        """Fetches on-chain veNFT data for an account address."""
        token_ids = cls._fetch_token_ids(address.lower())

        if len(token_ids) == 0:
            return []

        calls = []

        for token_id in token_ids:
            token_calls = [
                Call(
                    VE_ADDRESS,
                    ['decimals()(uint256)'],
                    [['token_%s_decimals' % token_id, None]]
                ),
                Call(
                    VE_ADDRESS,
                    ['balanceOfNFT(uint256)(uint256)', token_id],
                    [['token_%s_amount' % token_id, None]]
                ),
                Call(
                    VE_ADDRESS,
                    ['locked(uint256)(int128,uint256)', token_id],
                    [
                        ['token_%s_voting_amount' % token_id, None],
                        ['token_%s_lock_ends_at' % token_id, None]
                    ]
                ),
                Call(
                    VOTER_ADDRESS,
                    ['lastVoted(uint256)(uint256)', token_id],
                    [['token_%s_voted_at' % token_id, None]]
                ),
            ]

            calls.extend(token_calls)

        multi_data = Multicall(calls)()

        LOGGER.debug('Fetched %s %ss.', len(token_ids), cls.__name__)

        venfts = []

        for token_id in token_ids:
            token_prefix = 'token_%s_' % token_id
            token_data = {
                k.removeprefix(token_prefix): v
                for (k, v) in multi_data.items() if token_prefix in k
            }

            venfts.append(cls._from_data(address, token_id, token_data))

        return venfts

    @classmethod
    def _from_data(cls, address, token_id, data):
        """Imports/creates a veNFT from provided data."""
        # Cleanup old data...
        try:
            cls.load(token_id).delete()
        except KeyError:
            pass

        data['token_id'] = token_id
        data['account_address'] = address
        data['amount'] /= (10.0**data['decimals'])

        if data['voting_amount']:
            data['voting_amount'] /= (10.0**data['decimals'])

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
