#! /usr/bin/python

from distutils.core import setup
import qapy

setup(name='qapy',
      version= qapy.__version__,
      description= 'Qarnot Computing SDK',
      author='Qarnot Computing',
      packages=['qapy'],
      requires=['requests'])
