#!/usr/bin/env python
"""Setuptools file."""

from distutils.core import setup
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
      install_requires=['requests'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Information Technology',
                   'License :: OSI Approved :: Apache Software License'],
      license='apache')
