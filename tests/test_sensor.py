import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

import autopylot.config as config
import autopylot
import autopylot.sensor as sensor


class TestSensorGyrosensor(unittest.TestCase):
    """ Class to test the gyrosensor class """
    def setUp(self):
        self.gyrosensor = sensor.Gyrosensor(config.get_gyrosensor_address())

    def tearDown(self):
        self.gyrosensor = None

    def test_get_sensor_temperature(self):
        """ Tests if the gyrosensor returns valid temperature values in °C """
        temp = round(self.gyrosensor.get_sensor_temperature(), 0)
        # this test should be run in a room so i expect values
        # within "room temperature"
        in_range = temp in range(18, 30)
        self.assertTrue(in_range)

    def test_perform_selfcheck(self):
        """ Tests if the selfcheck is working as expected """
        # self.assertTrue(self.gyrosensor._perform_selfcheck())


if __name__ == '__main__':
        unittest.main()
