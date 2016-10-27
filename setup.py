#! /usr/bin/python

import versioneer
from distutils.core import setup
from os import mkdir, path
from setuptools.command.test import test as TestCommand
from subprocess import Popen, PIPE
import shutil
import sys




class PyTest(TestCommand):

    """Integration of PyTest with setuptools."""

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        """Initialize options."""
        TestCommand.initialize_options(self)
        try:
            from ConfigParser import ConfigParser
        except ImportError:
            from configparser import ConfigParser
        config = ConfigParser()
        config.read("pytest.ini")
        self.pytest_args = config.get("pytest", "addopts").split(" ")

    def finalize_options(self):
        """Finalize options."""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """Run tests."""
        # import here, cause outside the eggs aren't loaded
        import pytest
        shutil.rmtree('tests/tmp', ignore_errors=True)
        mkdir('tests/tmp')
        errno = pytest.main(self.pytest_args)
        shutil.rmtree('tests/tmp', ignore_errors=True)
        sys.exit(errno)

with open(path.join(path.dirname(__file__), 'README.rst')) as long_d_f:
    long_description = long_d_f.read()

setup(name='qarnot',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description= 'Qarnot Computing SDK',
      long_description= long_description,
      author='Qarnot Computing',
      author_email='support@qarnot-computing.com',
      url='http://computing.qarnot.com',
      packages=['qarnot'],
      requires=['requests'],
      license='apache')
