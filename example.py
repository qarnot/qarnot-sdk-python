#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qapy
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

if __name__ == "__main__":
    warnings.simplefilter("ignore", InsecureRequestWarning)
    #remporary workaround for certificate issue
    q = qapy.QConnection('example/qarnot.conf')
    with q.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script.py")
        task.constants['PYTHON_SCRIPT'] = "script.py"
        task.submit()
        task.wait()
        print(task.stdout, end='')
        for fInfo in task.results.list_files():
            with open(task.results[fInfo]) as f:
                print(f.read())
