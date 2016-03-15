# -*- coding: utf-8 -*-
""" setup settings """
from setuptools import setup

try:
    LONG_DESCRIPTION = open("README.rst").read()
except IOError:
    LONG_DESCRIPTION = ""

setup(
    name="cp-expand-includes",
    version="0.2.0",
    description="Expand includes for competitive programming",
    license="MIT",
    author="Roberto Sales",
    packages=['exinc'],
    entry_points = {
        "console_scripts": ['exinc = exinc.tool:entry_point']
    },
    install_requires=["argparse"],
    long_description=LONG_DESCRIPTION,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ]
)
