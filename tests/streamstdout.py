#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import time
import qapy
from os import walk
from os.path import join

if __name__ == "__main__":
    q = qapy.QApy('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script_verbose.py")
        task.constants['PYTHON_SCRIPT'] = "script_verbose.py"
        task.submit()

        while not task.wait(5):
            print(task.fresh_stdout(), end='')

        out = task.download_results("output/")

        print(task.fresh_stdout(), end='')
        for dirname, dirs, files in walk(out):
            for filename in files:
                with open(join(dirname,filename)) as f:
                    print(f.read())
