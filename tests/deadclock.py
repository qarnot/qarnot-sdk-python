#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qarnot
from qarnot.disk import UploadMode
from os import walk
from os.path import join

if __name__ == "__main__":
    q = qarnot.QApy('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script.py",
                                mode=UploadMode.background)
        task.constants['PYTHON_SCRIPT'] = "script.py"
        task.submit()
        task.wait()
        out = task.download_results("output/")
        print(task.stdout(), end='')
        print(task.stderr(), end='')
        for dirname, dirs, files in walk(out):
            for filename in files:
                with open(join(dirname,filename)) as f:
                    print(f.read())
