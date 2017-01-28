import unittest
import os
import sys
import configparser

sys.path.insert(0, os.path.abspath('..'))

import autopylot
import autopylot.config as config


class TestControlMotor(unittest.TestCase):
    """ Class to test the motor control class """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_verify_config(self):
        """ Checks if the verify_config_ini is doing it's job """
        valid_config_str = """
            [PIN]
            MotorFrontLeft = 4
            MotorFrontRight = 17
            MotorBackLeft = 22
            MotorBackRight = 27

            [GYRO]
            Address = 0x68
            TiltFront = +y
            TiltLeft = +x

            [ESC]
            Minimum = 1068
            Maximum = 1860

            [AERO]
            PropSize = 11x5

            [LOG]
            OutputFile = autopylot.log
            Level = debug

            [PIGPIOD]
            SampleRate = 1
        """
        valid_config = configparser.ConfigParser()
        valid_config.read_string(valid_config_str)
        self.assertTrue(config.verify_config_ini(valid_config))

    def test_verify_config_exception(self):
        """ Checks if the verify_config_ini raises an Exception as expected """
        invalid_config_str = """
            [PIN]
            MotorFrontLeft = 4
            MotorFrontRight = 17
            MotorBackLeft = 22
            MotorBackRight = 27

            [GYRO]
            Address = 0x68
            TiltFront = +y
            TiltLeft = +x

            [ESC]
            Minimum = 1068asdf
            Maximum = 1860

            [AERO]
            PropSize = 11x5

            [LOG]
            OutputFile = autopylot.log
            Level = nothing

            [PIGPIOD]
            SampleRate = 1
        """
        invalid_config = configparser.ConfigParser()
        invalid_config.read_string(invalid_config_str)
        with self.assertRaises(Exception):
            self.assertFalse(config.verify_config_ini(invalid_config))


if __name__ == '__main__':
        unittest.main()
