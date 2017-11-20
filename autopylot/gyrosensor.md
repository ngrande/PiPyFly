# Gyrosensor
This document describes some ideas from me on how to use the gyro sensor data for the drone

## Motion Tracking Model
Create a module which translates the acceleration and gyroscope data into a motion.
To hold a 0 (zero) point we just have to track each motion and have to tell the drone to do a counterpart to this.

For example a motion of +10x/s for 2 seconds will need a motion from our drone of -10x/s to get to the zero point again.

This means we simply have to track each motion and calculate the current position of the drone to know how to react to it.

### Using Acceleration Data
The acceleration data (in G) will tell us how fast the motion was performed - the faster the motion the stronger we have to react -> the motors of the drone have to throttle higher than with a slow motion (low G).

### Formula
#### Distance

    velocity = sum(acceleration)
    distance = sum(velocity)

#### Angular change

    tilt = sum(rotation)
