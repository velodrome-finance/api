# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import falcon
from healthcheck import Healthcheck

app = falcon.App()
app.req_options.auto_parse_form_urlencoded = True
app.req_options.strip_url_path_trailing_slash = True
app.add_route('/healthcheck', Healthcheck())


if __name__ == '__main__':
    port = int(os.getenv('PORT') or 3000)
    print('Starting on port', port, '...')

    import bjoern
    bjoern.run(app, '', port)
