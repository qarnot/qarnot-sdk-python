#! /usr/bin/python
"""example script for api usage """

from __future__ import print_function

import qapy
import tempfile
from qapy.disk import QUploadMode
from os import walk
from os.path import join

def main():
    """main function"""
    qarnot = qapy.QApy('example/qarnot.conf')
    with qarnot.create_task("example task", "python", 3) as task:
        task.resources.add_file("example/script_verbose.py",
                                mode=QUploadMode.background)
        task.constants['PYTHON_SCRIPT'] = "script_verbose.py"

        print("Submit task")
        task.submit()

        print ("Wait task")
        while not task.wait(10):
            print (task.fresh_stdout())

            outdir = tempfile.mkdtemp()
            print ("Download resultuts to " + outdir)
            task.download_results(outdir)
            for dirname, _, files in walk(outdir):
                for filename in files:
                    with open(join(dirname, filename)) as file_:
                        print(file_.read())


if __name__ == "__main__":
    main()

