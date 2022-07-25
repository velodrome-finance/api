# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class AccountsTestCase(AppTestCase):
    def test_get_no_address(self):
        result = self.simulate_get('/api/v1/accounts')

        self.assertEqual(type(result.json['data']), list)
        self.assertEqual(len(result.json['data']), 0)

    def test_get_wrong_address(self):
        result = self.simulate_get('/api/v1/accounts')

        self.assertEqual(type(result.json['data']), list)
        self.assertEqual(len(result.json['data']), 0)

    def test_get(self):
        result = self.simulate_get(
            '/api/v1/accounts'
            '?address=0xe247340f06fcb7eb904f16a48c548221375b5b96'
        )

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 20)
