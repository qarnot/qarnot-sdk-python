Installation
============

We recommend you to set up a Python virtual environment.
To do so you need `virtualenv`, you should be able to install it using for
example one of the following commands:

.. code-block:: bash

   $ apt-get install python-virtualenv
   $ easy_install virtualenv
   $ pip install virtualenv


Once `virtualenv` is installed you can create your own environment by running
the following commands in the project directory.

.. code-block:: bash

   $ virtualenv venv
   New python executable in venv/bin/python
   Installing setuptools, pip, wheel...done.

Then each time you want to use your virtual environment you have to activate it
by running this command:

.. code-block:: bash

   $ . venv/bin/activate

Finally you have to install in your environment the required dependencies running:

.. code-block:: bash

   pip install -r requirements.txt

If you plan to send large files to the API, we advise you to install the
optional requests-toolbelt dependency in order not to overuse your memory:

.. code-block:: bash

   pip install -r requirements-optional.txt

You are now ready to use the Qarnot SDK.
