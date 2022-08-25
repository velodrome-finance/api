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
            '?address=0x892ff98a46e5bd141e2d12618f4b2fe6284debac'
        )

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)

        flat_rewards = []
        for venft in result.json['data']:
            flat_rewards += venft['rewards']

        self.assertTrue(len(flat_rewards) > 1)
