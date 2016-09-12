#! /usr/bin/python

import versioneer
from distutils.core import setup

cmdclass=versioneer.get_cmdclass()

setup(name='qarnot',
      version=versioneer.get_version(),
      cmdclass=cmdclass,
      description= 'Qarnot Computing SDK',
      author='Qarnot Computing',
      author_email='support@qarnot-computing.com',
      url='http://computing.qarnot.com',
      packages=['qarnot'],
      requires=['requests'])
