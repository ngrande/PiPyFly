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
			[MOTORS.PIN]
			motorfrontleft = 4
			motorfrontright = 17
			motorrearleft = 22
			motorrearright = 27

			[MOTORS.ROTATION]
			motorfrontleft = CW
			motorfrontright = CCW
			motorrearleft = CCW
			motorrearright = CW

			[GYRO]
			address = 0x68
			tiltfront = +y
			tiltleft = +x

			[ESC]
			minimum = 1068
			maximum = 1860

			[AERO]
			propsize = 11x5

			[LOG]
			outputfile = autopylot.log
			level = debug

			[PIGPIOD]
			samplerate = 1
		"""
		valid_config = configparser.ConfigParser()
		valid_config.read_string(valid_config_str)
		self.assertTrue(config.verify_config_ini(valid_config))

	def test_verify_config_exception(self):
		""" Checks if the verify_config_ini raises an Exception as expected """
		invalid_config_str = """
			[PIN]
			motorfrontleft = 4
			motorfrontright = 17
			motorrearleft = 22
			motorrearright = 27

			[MOTORS.ROTATION]
			motorfrontleft = yCW
			motorfrontright = CCW
			motorrearleft = CCW
			motorrearright = CW

			[GYRO]
			address = 0x68
			tiltfront = +y
			tiltleft = +x

			[ESC]
			minimum = 1068asdf
			maximum = 1860

			[AERO]
			propsize = 11x5

			[LOG]
			outputfile = autopylot.log
			level = nothing

			[PIGPIOD]
			samplerate = 1
		"""
		invalid_config = configparser.ConfigParser()
		invalid_config.read_string(invalid_config_str)
		with self.assertRaises(Exception):
			self.assertFalse(config.verify_config_ini(invalid_config))


if __name__ == '__main__':
		unittest.main()

# vim: tabstop=4 shiftwidth=4 noexpandtab
