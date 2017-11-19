""" module to assist the quadcopter. It will use the sensor data to calculate
the correct throtte values for the motors """

import autopylot.control
import autopylot.sensor
import autopylot.config

class Assistant():
	def __init__(self):
		self._gyro_sensor = self._init_gyrosensor()

	def _init_gyrosensor(self):
		""" Returns an initialized Gyrosensor object """
		address = autopylot.config.get_gyrosensor_address()
		return autopylot.sensor.Gyrosensor(address)

	def keep_hovering(self):
		""" tries to hold the drone as steady as possible 
		in the same position """
		gyro_data = self._gyro_sensor.get_gyroscope_data()
		accel_data = self._gyro_sensor.get_acceleration_data()

# vim: tabstop=4 shiftwidth=4 noexpandtab
