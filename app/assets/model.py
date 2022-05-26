# -*- coding: utf-8 -*-

from multicall import Call, Multicall
import requests
from walrus import Model, TextField, IntegerField
from web3.auto import w3

from app.settings import LOGGER, CACHE, TOKENLISTS


class Token(Model):
    """ERC20 token model."""
    __database__ = CACHE

    address = TextField(primary_key=True)
    name = TextField()
    symbol = TextField()
    decimals = IntegerField()
    logoURI = TextField()

    @classmethod
    def find(cls, address):
        """Loads a token from the database, of from chain if not found."""
        try:
            return cls.load(address)
        except KeyError:
            return cls.from_chain(address)

    @classmethod
    def from_chain(cls, address):
        """Fetches and returns a token from chain."""
        token_multi = Multicall([
            Call(address, ['name()(string)'], [['name', None]]),
            Call(address, ['symbol()(string)'], [['symbol', None]]),
            Call(address, ['decimals()(uint8)'], [['decimals', None]])
        ])

        data = token_multi()

        # TODO: Add a dummy logo...
        token = cls.create(address=address, **data)

        LOGGER.debug('Fetched %s:%s.', cls.__name__, address)

        return token

    @classmethod
    def from_tokenlists(cls):
        """Fetches and merges all the tokens from available tokenlists."""
        our_chain_id = w3.eth.chain_id

        for tlist in TOKENLISTS:
            try:
                res = requests.get(tlist).json()
                for token_data in res['tokens']:
                    # Skip tokens from other chains...
                    if token_data.get('chainId', None) != our_chain_id:
                        continue

                    token_data['address'] = token_data['address'].lower()
                    cls.create(**token_data)

                    LOGGER.debug(
                        'Loaded %s:%s.', cls.__name__, token_data['address']
                    )
            except Exception as error:
                LOGGER.error(error)
                continue
