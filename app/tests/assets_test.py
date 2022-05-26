# -*- coding: utf-8 -*-

from web3.auto import w3

from .helpers import AppTestCase


class AssetsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/assets')
        our_chain_id = w3.eth.chain_id

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)

        for token in result.json['data']:
            self.assertEqual(token['chainId'], our_chain_id)
