# -*- coding: utf-8 -*-

import time
import sys

from multicall import Call

from app.pairs import Pairs, Pair
from app.assets import Token
from app.gauges import Gauge
from app.settings import CACHE, LOGGER, SYNC_WAIT_SECONDS, VOTER_ADDRESS


def sync():
    """Syncs """
    Token.from_tokenlists()
    Pair.chain_syncup()
    # Reset any cache...
    CACHE.delete(Pairs.CACHE_KEY)

    # Distribute any emissions to the gauges...
    Call(
        VOTER_ADDRESS,
        ['distribute(uint256,uint256)()', 0, Gauge.count()],
        [[]]
    )()


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
