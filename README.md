# PiPyFly
Create a Multicopter using a RaspberryPi

## Work in progress
![quadcopter top view](doc/pics/IMG_20170121_224149.jpg "Quadcopter top view")

# Setup
install the python package via ``` make install ```
__make sure to start the pigpiod daemon__ to be able to control the pins
which is included in the pigpio python module

for example you could put it in your /etc/rc.local file

    pigpiod -s 1

this will start the daemon with a sampling rate of 1 (the lowest possible)

# Tests
run the tests via ``` make test ```
