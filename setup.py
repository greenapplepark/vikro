#!/usr/bin/env python
import os
from setuptools import setup, find_packages

from vikro import __version__

setup(
    name='Vikro',
    version=__version__,
    author='Keke Xiang',
    author_email='xiangkeke@gmail.com',
    description='Lightweight micro service framework',
    packages=find_packages(),
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    entry_points={
        'console_scripts': [
            'vikro = vikro.runner:run_vikro',
            'vikromgr = vikro.runner:run_vikromgr'
        ]
    },
)