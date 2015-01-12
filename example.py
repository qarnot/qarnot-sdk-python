#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qapy
import tempfile
from qapy.disk import QAddMode
from os import walk
from os.path import join

if __name__ == "__main__":
    q = qapy.QApy('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script.py", mode=QAddMode.background)
        task.constants['PYTHON_SCRIPT'] = "script.py"
        out = task.submit(tempfile.mkdtemp())
        print(task.stdout, end='')
        for dirname, dirs, files in walk(out):
            for filename in files:
                with open(join(dirname,filename)) as f:
                    print(f.read())
