# -*- coding: utf-8 -*-

import os
from multiprocessing import Process
from multiprocessing.pool import ThreadPool
import time

from app.pairs import Pairs, Pair
from app.assets import Assets, Token
from app.settings import (
    LOGGER, SYNC_WAIT_SECONDS
)


def sync():
    """Syncs """
    LOGGER.info('Syncing pairs ...')
    t0 = time.time()

    Token.from_tokenlists()
    Assets.recache()
    LOGGER.info('Syncing tokens done in %s seconds.', time.time() - t0)

    with ThreadPool(int(os.getenv('SYNC_MAX_THREADS', 4))) as pool:
        addresses = Pair.chain_addresses()

        LOGGER.debug(
            'Syncing %s pairs using %s threads...',
            len(addresses),
            pool._processes
        )

        pool.map(Pair.from_chain, addresses)
        pool.close()
        pool.join()

    Pairs.recache()
    LOGGER.info('Syncing pairs done in %s seconds.', time.time() - t0)


def sync_forever():
    LOGGER.info('Syncing every %s seconds ...', SYNC_WAIT_SECONDS)

    while True:
        sync_proc = Process(target=sync)
        try:
            sync_proc.start()
            sync_proc.join()
        except KeyboardInterrupt:
            LOGGER.info('Syncing stopped!')
            break
        except Exception as error:
            LOGGER.error(error)
        finally:
            sync_proc.terminate()
            sync_proc.join()
            sync_proc.close()
            del sync_proc

        time.sleep(SYNC_WAIT_SECONDS)


if __name__ == '__main__':
    if SYNC_WAIT_SECONDS < 1:
        sync()
    else:
        sync_forever()
