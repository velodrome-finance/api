# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class ConfigurationTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/configuration')

        self.assertTrue(len(result.json['data']) > 0)
        self.assertIsNotNone(result.json['meta']['version'])
