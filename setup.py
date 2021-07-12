#!/usr/bin/env python
"""Setuptools file."""

# pylint: disable=E0611,F0401
from setuptools import setup
from os import path
import versioneer

try:
    import setuptools
    [setuptools]
except ImportError:
    pass

with open(path.join(path.dirname(__file__), 'README.rst')) as long_d_f:
    LONG_DESCRIPTION = long_d_f.read()

setup(name='qarnot',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Qarnot Computing SDK',
      long_description=LONG_DESCRIPTION,
      author='Qarnot computing',
      author_email='support@qarnot-computing.com',
      url='https://computing.qarnot.com',
      packages=['qarnot'],
      install_requires=['requests', 'boto3'],
      tests_require=['pytest'],
      python_requires='>=3.6',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Information Technology',
                   'License :: OSI Approved :: Apache Software License'],
      license='apache')
