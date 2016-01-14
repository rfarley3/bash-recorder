#!/usr/bin/env python

from setuptools import setup

setup(
    name='bash_recorder',
    version='0.0.2',
    description='Record all bash history and upload to a REST server',
    author='Ryan Farley',
    author_email='rfarley@mitre.org',
    py_modules=['bash_recorder'],
    install_requires=(
        'requests',
        'bottle',
    ),
    entry_points={
        'console_scripts': [
            'bashrecorder = bash_recorder:main',
        ]
    },
)
