Basic usage
===========

Configuration
-------------

A basic usage of the Qarnot require a configuration file (eg: `qarnot.conf`).
Here is a basic one, check :class:`~qarnot.connection.QApy` for details.

.. code-block:: ini
   :linenos:

   [cluster]
   # url of the REST API
   url=https://rest01.qarnot.net
   [client]
   # auth string of the client
   auth=token

Script
------

And here is a little sample to start a task running your `myscript.py` Python script.

.. code-block:: python
   :linenos:

   import qarnot
   import tempfile

    qarnot = qarnot.QApy('qarnot.conf')
    with qarnot.create_task("example task", "python", 1) as task:
        task.resources.add_file("myscript.py")
        task.constants['PYTHON_SCRIPT'] = "myscript.py"

        print "Submit task"
        task.submit()

        print ("Wait task results")
        while not task.wait(10):
            print task.fresh_stdout()

        outdir = tempfile.mkdtemp()
        print "Download results to " + outdir
        task.download_results(outdir)

