# -*- coding: utf-8 -*-

import json
import datetime
import decimal


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for decimals."""
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
