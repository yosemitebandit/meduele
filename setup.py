#!/usr/bin/env python
from meduele import __version__

options = {
    'name': 'meduele',
    'version': __version__,
    'description': 'server and backend for the meduele service',
    'packages': ['meduele']
}

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(**options)
