# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='HTTP API',
    packages=find_packages(include=['app', 'app.*']),
    include_package_data=True,
    install_requires=(
        'wsgi-request-logger',
        'versiontools',
        'falcon == 3.1',
        'falcon-compression == 0.2.1',
        'bjoern == 3.2.1',
        'web3',
        'multicall @ https://codeload.github.com/velodrome-finance/multicall.py/zip/refs/heads/optimism_version_bump#egg=multicall-0.5.2',  # noqa
        'redis == 4.2.2',
        'fakeredis == 1.7.4',
        'walrus == 0.9.1',
        'honeybadger == 0.8.0'
    ),
    version=":versiontools:app"
)
