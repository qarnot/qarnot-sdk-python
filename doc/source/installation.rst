Installation
============

We recommend you to set up a Python virtual environment.
To do so with Python2 you need `virtualenv`, you should be able to install it using for
example one of the following commands:

.. code-block:: bash

   $ apt-get install python-virtualenv
   $ easy_install virtualenv
   $ pip install virtualenv

Or for Python3:

.. code-block:: bash

   $ apt-get install python3-venv
   $ pip3 install virtualenv

Once `virtualenv` is installed you can create your own environment by running
the following commands in the project directory:

.. code-block:: bash

   $ virtualenv venv
   New python executable in venv/bin/python
   Installing setuptools, pip, wheel...done.

Or with Python3;

.. code-block:: bash

   $ python3 -m venv venv

Then each time you want to use your virtual environment you have to activate it
by running this command:

.. code-block:: bash

   $ . venv/bin/activate

Finally you have to install in your environment the Qarnot SDK:

.. code-block:: bash

   pip install qarnot

If you plan to send large files to the API, we advise you to install the
optional requests-toolbelt dependency in order not to overuse your memory:

.. code-block:: bash

   pip install requests-toolbelt

You are now ready to use the Qarnot SDK.
