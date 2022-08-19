# -*- coding: utf-8 -*-

from app.assets import Token
from app.settings import IGNORED_TOKEN_ADDRESSES

from .helpers import AppTestCase


class AssetsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/assets')

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)

        for ignored in IGNORED_TOKEN_ADDRESSES:
            self.assertEqual(
                len(list(Token.query(Token.address == ignored))),
                0
            )
