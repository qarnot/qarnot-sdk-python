#! /usr/bin/python
"""example script for api usage """

import qapy

if __name__ == "__main__":
    try:
        q = qapy.QConnection('https://localhost', 'second')
        task = q.create_task("example task", "python", 3)
        task.resources.add_file("example/script.py")
        task.constants['PYTHON_SCRIPT'] = "script.py"
        task.submit()
        task.wait()
        print(task.stdout)
        for fInfo in task.results.list_files():
            with open(task.results[fInfo]) as f:
                print(f.read())
    finally:
        task.delete()
