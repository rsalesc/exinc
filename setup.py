# -*- coding: utf-8 -*-
""" setup settings """
from setuptools import setup

try:
    LONG_DESCRIPTION = open("README.rst").read()
except IOError:
    LONG_DESCRIPTION = ""

setup(
    name="cp-expand-includes",
    version="0.1.0",
    description="Expand includes for competitive programming",
    license="MIT",
    author="Roberto Sales",
    packages=['expand'],
    entry_points = {
        "console_scripts": ['exinc = expand.tool:entry_point']
    },
    install_requires=["argparse"],
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ]
)
