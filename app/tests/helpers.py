# -*- coding: utf-8 -*-

from falcon import testing

from app.app import app


class AppTestCase(testing.TestCase):
    """Default app test-case."""

    def setUp(self):
        """Test setup."""
        super(AppTestCase, self).setUp()
        self.app = app
