# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class ConfigurationTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/configuration')

        self.assertTrue(result.json['meta']['tvl'] > 0)
        self.assertTrue(result.json['meta']['max_apr'] > 0)
        self.assertIsNotNone(result.json['meta']['version'])
        self.assertFalse(result.json['meta']['cache'])
