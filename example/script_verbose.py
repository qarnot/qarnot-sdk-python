#! /usr/bin/python
import time
import os

if __name__ == "__main__":
    frame_id = os.environ.get('QRANK', '0')
    print('frame %s starting' % frame_id)
    time.sleep(42 * (int(os.environ.get('QRANK', 0)) + 1))
    print('opening %s' % (frame_id + ".output"))
    with open(frame_id + ".output", 'w') as f:
        f.write(frame_id)
    print('frame %s finished' % frame_id)
