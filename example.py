#! /usr/bin/python
"""example script for api usage """

import apy

if __name__ == "__main__":
    q = apy.QConnection('https://localhost', 'second')
    task = apy.QTask(q, "example task", "python", 2)
    task.resources.add_file("example/script.py")
    task.constants['PYTHON_SCRIPT'] = "script.py"
    task.submit()
    task.wait()
    for fInfo in task.results.list_files():
        with open(task.results[fInfo]) as f:
            print(f.read())
    task.delete()
