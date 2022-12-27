# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='HTTP API',
    packages=find_packages(include=['app', 'app.*']),
    include_package_data=True,
    # TODO: Unpin web3 and eth_retry when folks fix the issues
    #       https://github.com/banteg/multicall.py/issues/53
    #       https://github.com/BobTheBuidler/eth_retry/issues/20
    install_requires=(
        'wsgi-request-logger',
        'versiontools',
        'falcon == 3.1.1',
        'falcon-compression == 0.2.1',
        'bjoern == 3.2.2',
        'web3 == 5.27',
        'eth_retry == 0.1.13',
        'multicall == 0.7',
        'redis == 4.4.0',
        'fakeredis == 2.4.0',
        'walrus == 0.9.2',
        'honeybadger == 0.14.0'
    ),
    version=":versiontools:app"
)
