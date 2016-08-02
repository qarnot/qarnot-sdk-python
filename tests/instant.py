#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import time

import qarnot
from qarnot.disk import UploadMode
from os import walk, listdir
from os.path import join

if __name__ == "__main__":
    q = qarnot.QApy('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script.py", mode=UploadMode.background)
        task.constants['PYTHON_SCRIPT'] = "script.py"
        task.submit()
        time.sleep(84)
        task.instant()
        print(listdir(task.results()))
        task.wait()
        print(task.stdout(), end='')
        out = task.download_results("output/")
        for dirname, _, files in walk(out):
            for filename in files:
                with open(join(dirname,filename)) as f:
                    print(f.read())
