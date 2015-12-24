#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from setuptools import setup
except ImportError:
    print('Fatal error - Missing library "setuptools". Please install the required libraries before re-attempting this installation.')
    sys.exit(1)

required_libs = ['pyvmomi==5.5.0.2014.1.1','python-dateutil>=2.4.2', 'requests>=2.0.0']
packages = []

setup(
    name='TSPulse VMWare Plugin',
    version='1.0.0',
    author='R&D, BMC Software',
    author_email='support@bmc.com',
    description='VMWare plugin for BMC TrueSight Pulse',
    keywords=['TSP-VMWare'],
    url='http://www.bmc.com',
    install_requires=required_libs,
    packages=packages
)
