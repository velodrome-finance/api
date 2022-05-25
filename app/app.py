# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
from logging import StreamHandler

import falcon
from requestlogger import WSGILogger, ApacheFormatter

from app.assets import Assets
from app.configuration import Configuration
from app.pairs import Pairs
from app.settings import LOGGER

app = falcon.App(cors_enable=True)
app.req_options.auto_parse_form_urlencoded = True
app.req_options.strip_url_path_trailing_slash = True
app.add_route('/assets', Assets())
app.add_route('/configuration', Configuration())
app.add_route('/pairs', Pairs())

# Wrap the app in a WSGI logger to make it more verbose...
app = WSGILogger(app, [StreamHandler(sys.stdout)], ApacheFormatter())

if __name__ == '__main__':
    port = int(os.getenv('PORT') or 3000)
    LOGGER.info('Starting on port %s ...', port)

    import bjoern
    bjoern.run(app, '', port, reuse_port=True)
