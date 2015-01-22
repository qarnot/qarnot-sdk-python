#! /usr/bin/python

from distutils.core import setup
import qapy

setup(name='qapy',
      version= qapy.__version__,
      description= 'qarnot computing task api',
      author='Michael Willame',
      packages=['qapy'],
      requires=['requests', 'enum34'])
