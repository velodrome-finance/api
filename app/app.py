# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
from logging import StreamHandler

import falcon
from requestlogger import WSGILogger, ApacheFormatter
from falcon_compression.middleware import CompressionMiddleware

from app.assets import Assets
from app.configuration import Configuration
from app.pairs import Pairs
from app.settings import LOGGER, honeybadger_handler
from app.venfts import Accounts

app = falcon.App(cors_enable=True, middleware=[CompressionMiddleware()])
app.add_error_handler(Exception, honeybadger_handler)
app.req_options.auto_parse_form_urlencoded = True
app.req_options.strip_url_path_trailing_slash = True
app.add_route('/api/v1/accounts', Accounts())
app.add_route('/api/v1/assets', Assets())
app.add_route('/api/v1/configuration', Configuration())
app.add_route('/api/v1/pairs', Pairs())

# TODO: Remove when no longer needed for backward-compat...
app.add_route('/api/v1/baseAssets', Assets())
app.add_route('/api/v1/routeAssets', Configuration())
app.add_route('/api/v1/updatePairs', Pairs())

# Wrap the app in a WSGI logger to make it more verbose...
wsgi = WSGILogger(app, [StreamHandler(sys.stdout)], ApacheFormatter())

if __name__ == '__main__':
    port = int(os.getenv('PORT') or 3000)
    LOGGER.info('Starting on port %s ...', port)

    import bjoern
    bjoern.run(wsgi, '', port, reuse_port=True)
