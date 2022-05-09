import falcon


class Healthcheck(object):
    """Simple health/status check"""

    @staticmethod
    def on_get(req, resp):
        resp.status = falcon.HTTP_200
        resp.body = 'OK'
