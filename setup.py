#!/usr/bin/env python3

import os
from setuptools import setup


def load_file_content(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="PiPyFly",
    version="0.0.1",
    author="Niclas Grande",
    author_email="devlup@outlook.com",
    description="Python package to control a RaspberryPi based quadcopter",
    license=load_file_content("LICENSE"),
    keywords="raspberrypi quadcopter multirotor",
    url="https://github.com/ngrande/PiPyFly",
    packages=["autopylot", "tests"],
    long_description=load_file_content("README.md"),
    install_requires=['pigpio', 'psutil', 'mpu6050-raspberrypi'],
    tests_require=['pigpio'],
    test_suite='tests',
    # classifiers = [""]
)
