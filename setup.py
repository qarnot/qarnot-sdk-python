#! /usr/bin/python

from distutils.core import setup
from os import mkdir
from setuptools.command.test import test as TestCommand
import shutil
import sys

import qapy


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

setup(name='qapy',
      version= qapy.__version__,
      description= 'Qarnot Computing SDK',
      author='Qarnot Computing',
      packages=['qapy'],
      requires=['requests'],
      tests_require=['pytest', 'pytest-cov'],
      cmdclass = {'test': PyTest})
