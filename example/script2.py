#! /usr/bin/python
import time
import os
from sys import stderr

if __name__ == "__main__":
    frame_id = os.environ.get('QRANK', '0')
    for i in range((1 + int(os.environ.get('QRANK', 0))) * 2):
        time.sleep(1)
        print >> stderr, "i am frame {} at iter {}".format(frame_id, i)
