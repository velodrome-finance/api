# -*- coding: utf-8 -*-

from .helpers import AppTestCase


class AssetsTestCase(AppTestCase):
    def test_get(self):
        result = self.simulate_get('/assets')

        self.assertEqual(type(result.json['data']), list)
        self.assertEqual(len(result.json['data']), 126)
