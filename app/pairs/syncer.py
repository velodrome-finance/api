# -*- coding: utf-8 -*-

import time
import sys

from app.pairs import Pairs
from app.settings import LOGGER, SYNC_WAIT_SECONDS


if __name__ == '__main__':
    if SYNC_WAIT_SECONDS < 1:
        LOGGER.info('Syncing is disabled!')
        sys.exit(0)

    LOGGER.info('Syncing every %s seconds ...', SYNC_WAIT_SECONDS)

    while True:
        LOGGER.info('Syncing pairs...')

        try:
            Pairs.pairs(force_sync=True)
            LOGGER.info('Syncing pairs done.')
        except KeyboardInterrupt:
            LOGGER.info('Syncing stopped!')
            break

        time.sleep(SYNC_WAIT_SECONDS)
