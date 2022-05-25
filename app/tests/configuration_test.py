# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class ConfigurationTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/configuration')

        self.assertIsNotNone(result.json['meta']['version'])
        self.assertFalse(result.json['meta']['cache'])
