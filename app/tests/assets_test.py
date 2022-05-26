# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class AssetsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/api/v1/assets')

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)
