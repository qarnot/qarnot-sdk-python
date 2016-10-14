Basic usage
===========

Configuration
-------------

A basic usage of the Qarnot require a configuration file (eg: `qarnot.conf`).
Here is a basic one, check :class:`~qarnot.connection.Connection` for details.

.. code-block:: ini
   :linenos:

   [cluster]
   # url of the REST API
   url=https://api.qarnot.com
   [client]
   # auth string of the client
   token=token

Script
------

And here is a little sample to start a task running your `myscript.py` Python script.

.. code-block:: python
   :linenos:

   import qarnot

    conn = qarnot.connection.Connection('qarnot.conf')
    task = conn.create_task('hello world', 'ubuntu')
    task.constants['DOCKER_CMD'] = 'echo hello world from ${FRAME_ID}!'
    task.run()
    print(task.stdout())
