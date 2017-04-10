Qarnot computing Python SDK
===========================

|travis-badge|_ |pypi-badge|_ |readthedocs-badge|_

This package allows you to use Qarnot cloud computing service.

You can launch, manage and monitor payloads running on distributed computing nodes deployed in Qarnot’s `digital heaters <http://www.qarnot.com/qrad>`_.

Basic usage
===========

Get your token and free computation time on `computing.qarnot.com <https://computing.qarnot.com>`_

Launch a docker container in 7 lines:

.. code:: python

    import qarnot
    conn = qarnot.connection.Connection({'client_auth': 'xxxx-mytoken-xxxx'})
    task = conn.create_task('hello world', 'docker-batch', 4)
    task.constants["DOCKER_REPO"]="library/ubuntu"
    task.constants['DOCKER_CMD'] = 'echo hello world from node #${FRAME_ID}!'
    task.run()

Samples and documentations
==========================
You can find samples and detailed information on `computing.qarnot.com <https://computing.qarnot.com>`_.

SDK documentation is available `here <https://computing.qarnot.com/documentation/sdk-python/>`_

Generating documentation
========================

To generate the SDK documentation you can use the following command

.. code:: bash

    make -C doc html

The index of the doc is then generated in `doc/_build/html/index.html`

.. |pypi-badge| image:: https://img.shields.io/pypi/v/qarnot.svg
.. _pypi-badge: https://pypi.python.org/pypi/qarnot/
.. |readthedocs-badge| image:: https://readthedocs.org/projects/qarnot/badge/?version=latest
.. _readthedocs-badge: https://qarnot.readthedocs.io/en/latest/
.. |travis-badge| image:: https://travis-ci.org/qarnot/qarnot-sdk-python.svg?branch=master
.. _travis-badge: https://travis-ci.org/qarnot/qarnot-sdk-python
