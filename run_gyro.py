#!/usr/bin/env python3

import mpu6050.mpu6050 as sensor
import time


if __name__ == '__main__':
    gyro = sensor(0x68)
    while True:
        data = gyro.get_accel_data()
        x = int(round(data['x'], 0))
        y = int(round(data['y'], 0))
        z = int(round(data['z'], 0))
        print("X: {!s}\t\tY: {!s}\t\tZ: {!s}".format(x, y, z))
        time.sleep(1)
