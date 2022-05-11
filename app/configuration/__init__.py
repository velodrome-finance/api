# -*- coding: utf-8 -*-

import json

import falcon
from versiontools import Version

from assets import Assets
from settings import CACHE, DEFAULT_TOKEN_ADDRESS, \
    STABLE_TOKEN_ADDRESS, __version__


class Configuration(object):
    """Returns a app configuration object"""

    def on_get(self, req, resp):
        default_token=Assets.token_by_address(DEFAULT_TOKEN_ADDRESS)
        stable_token=Assets.token_by_address(STABLE_TOKEN_ADDRESS)

        resp.status = falcon.HTTP_200
        resp.text = json.dumps(
            dict(
                data=dict(
                    default_token=default_token,
                    stable_token=stable_token,
                    cache=(CACHE.connection is not None),
                    version=str(Version(*__version__))
                )
            )
        )
