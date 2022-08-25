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
            '?address=0x278B28459096f17b770ccFF0eaF71195080e89d1'
        )

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)

        flat_rewards = []
        for venft in result.json['data']:
            flat_rewards += venft['rewards']

        self.assertTrue(len(flat_rewards) > 1)
