#! /usr/bin/python
"""api equivalent of test.qsh"""

from __future__ import print_function

import qapy
import sys

if __name__ == '__main__':
    q = qapy.QApy('example/qarnot.conf')
    with q.create_task("blender test", "mwillame.blender-2.72", 4) as task:
        task.resources['main.blend'] = sys.argv[1]
        task.constants['BLEND_FILE'] = "main.blend"
        task.constants['BLEND_ENGINE'] = 'CYCLES'
        task.constants['BLEND_CYCLES_SAMPLES'] = '20'
        task.constants['BLEND_FORMAT'] = 'PNG'
        task.constants['BLEND_SCENE'] = 'titi'
        task.constants['BLEND_SLICING'] = '2'
        if len(sys.argv) > 2:
            task.advanced_range=sys.argv[2]

        task.submit('./results')

        print(task.stdout, end='')
        print(task.stderr, end='', file=sys.stderr)
