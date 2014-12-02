#! /usr/bin/python
import time
import os

if __name__ == "__main__":
    time.sleep(42 * (int(os.environ.get('QRANK', 0)) + 1))
    frame_id = os.environ.get('QRANK', '0')
    with open(frame_id + ".output", 'w') as f:
        f.write(frame_id)
