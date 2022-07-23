# -*- coding: utf-8 -*-

from multiprocessing import Process
import time
import sys

from multicall import Call

from app.pairs import Pairs, Pair
from app.assets import Assets, Token
from app.gauges import Gauge
from app.settings import (
    LOGGER, SYNC_WAIT_SECONDS, VOTER_ADDRESS, reset_multicall_pool_executor
)


def sync(force_shutdown=False):
    """Syncs """
    LOGGER.info('Syncing pairs ...')
    t0 = time.time()

    Token.from_tokenlists()
    Pair.chain_syncup()
    # Reset any cache...
    Pairs.recache()
    Assets.recache()

    # Distribute any emissions to the gauges...
    Call(
        VOTER_ADDRESS,
        ['distribute(uint256,uint256)()', 0, Gauge.count()],
        [[]]
    )()

    LOGGER.info('Syncing pairs done in %s seconds.', time.time() - t0)

    reset_multicall_pool_executor()


def sync_forever():
    if SYNC_WAIT_SECONDS < 1:
        LOGGER.info('Syncing is disabled!')
        sys.exit(0)

    LOGGER.info('Syncing every %s seconds ...', SYNC_WAIT_SECONDS)

    while True:
        sync_proc = Process(target=sync, args=(False,))
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
    sync_forever()
