# -*- coding: utf-8 -*-

from app.assets import Token
from app.settings import IGNORED_TOKEN_ADDRESSES

from .helpers import AppTestCase


class AssetsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/assets')

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)

        ignored = list(
            filter(lambda t: t.address in IGNORED_TOKEN_ADDRESSES, Token.all())
        )

        self.assertEqual(len(ignored), 0)

        zero_priced = list(filter(lambda t: t.price == 0, Token.all()))
        zero_priced_symbols = list(map(lambda t: t.symbol, zero_priced))

        self.assertFalse('BOND' in zero_priced_symbols)
