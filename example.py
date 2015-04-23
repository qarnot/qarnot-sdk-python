#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qapy
import tempfile
from qapy.disk import QUploadMode
from os import walk
from os.path import join

if __name__ == "__main__":
    q = qapy.QApy('example/qarnot.conf')
    task = q.create_task("example task", "python", 3)
    task.resources.add_file("example/script_verbose.py",
                            mode=QUploadMode.background)
    task.constants['PYTHON_SCRIPT'] = "script_verbose.py"
    out = tempfile.mkdtemp()
    task.submit(out)
    print ("out " + out)
    while not task.wait(10):
        print ("...")
        print (task.fresh_stdout())
    for dirname, dirs, files in walk(out):
        for filename in files:
            with open(join(dirname,filename)) as f:
                print(f.read())
    task.delete()
