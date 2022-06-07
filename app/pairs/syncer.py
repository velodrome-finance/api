# -*- coding: utf-8 -*-

from multiprocessing import Process
import time
import os

from multicall import Call

from app.pairs import Pairs, Pair
from app.assets import Token
from app.gauges import Gauge
from app.settings import CACHE, LOGGER, SYNC_WAIT_SECONDS, VOTER_ADDRESS


def sync(force_shutdown=False):
    """Syncs """
    LOGGER.info('Syncing pairs ...')
    t0 = time.time()

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

    LOGGER.info('Syncing pairs done in %s seconds.', time.time() - t0)

    # Multicall hangs so we need to force the event loop shutdown...
    if force_shutdown:
        os._exit(os.EX_OK)


def sync_forever():
    if SYNC_WAIT_SECONDS < 1:
        LOGGER.info('Syncing is disabled!')
        os._exit(os.EX_OK)

    LOGGER.info('Syncing every %s seconds ...', SYNC_WAIT_SECONDS)

    while True:
        LOGGER.debug('start')
        sync_proc = Process(target=sync, args=(True,))
        try:
            sync_proc.start()
            sync_proc.join()
        except KeyboardInterrupt:
            sync_proc.terminate()
            LOGGER.info('Syncing stopped!')
            break
        except:  # noqa
            sync_proc.terminate()
        finally:
            sync_proc.close()
            del sync_proc

        time.sleep(SYNC_WAIT_SECONDS)


if __name__ == '__main__':
    sync_forever()
