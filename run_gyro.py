#!/usr/bin/env python3

import autopylot.motion
import time


if __name__ == '__main__':
    mt = autopylot.motion.MotionTracker()
    while True:
        distance = mt.get_distance()
        tilt = mt.get_tilt()
        print("DISTANCE => X: {!s}\t\tY: {!s}\t\tZ: {!s}".format(
            distance['x'], 
            distance['y'], 
            distance['z']))
        print("")

        print("TILT => X: {!s}\t\tY: {!s}\t\tZ: {!s}".format(
            tilt['x'],
            tilt['y'],
            tilt['z']))
        time.sleep(1)
