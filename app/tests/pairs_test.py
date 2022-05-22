# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class PairsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/pairs')

        self.assertEqual(type(result.json['data']), list)
        self.assertTrue(len(result.json['data']) > 1)
