# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='HTTP API',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=(
        'versiontools',
        'falcon == 3.1',
        'bjoern == 3.2.1',
        'web3',
        'multicall == 0.4',
        'redis == 4.2.2',
        'fakeredis == 1.7.4'
    ),
    tests_require=(
        'flake8',
        'coverage'
    ),
    version = ":versiontools:.settings"
)
