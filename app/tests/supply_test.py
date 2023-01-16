# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class SupplyTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/supply')

        self.assertIsNotNone(result.json['data'])
        self.assertEqual(len(result.json['data']), 7)
        self.assertEqual(result.json['data']['token_decimals'], 18)
        self.assertEqual(result.json['data']['lock_decimals'], 18)
        self.assertTrue(result.json['data']['circulating_supply'] > 0)
