# -*- coding: utf-8 -*-

import time
import sys

from app.pairs import Pairs, Pair
from app.assets import Token
from app.settings import CACHE, LOGGER, SYNC_WAIT_SECONDS


def sync():
    """Syncs """
    Token.from_tokenlists()
    Pair.chain_syncup()
    # Reset any cache...
    CACHE.delete(Pairs.CACHE_KEY)


if __name__ == '__main__':
    if SYNC_WAIT_SECONDS < 1:
        LOGGER.info('Syncing is disabled!')
        sys.exit(0)

    LOGGER.info('Syncing every %s seconds ...', SYNC_WAIT_SECONDS)

    while True:
        LOGGER.info('Syncing pairs...')

        try:
            sync()
            LOGGER.info('Syncing pairs done.')
        except KeyboardInterrupt:
            LOGGER.info('Syncing stopped!')
            break
        except:  # noqa
            pass

        time.sleep(SYNC_WAIT_SECONDS)
