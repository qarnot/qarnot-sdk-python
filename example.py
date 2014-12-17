#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qapy
from qapy.disk import QAddMode

if __name__ == "__main__":
    q = qapy.QApy('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script.py", mode=QAddMode.background)
        task.constants['PYTHON_SCRIPT'] = "script.py"
        task.submit()
        task.wait()
        print(task.stderr, end='')
        for fInfo in task.results.list_files():
            with open(task.results[fInfo]) as f:
                print(f.read())
