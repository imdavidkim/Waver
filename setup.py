# -*- coding: utf-8 -*-
import unittest
from setuptools import setup, find_packages


def detective_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('test', pattern='test_*.py')
    return test_suite


MODULE_NAME = 'detective'
PACKAGE_DATA = list()
CLASSIFIERS = [
    'Development Status :: 1 - Alpha',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python',
    'Topic :: Utilities',
]


setup(
    name='detective',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    description='',
    classifiers=CLASSIFIERS,
)
