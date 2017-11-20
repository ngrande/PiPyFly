""" module to assist the quadcopter. It will use the sensor data to calculate
the correct throtte values for the motors """

import autopylot.control
import autopylot.sensor
import autopylot.config

class Assistant():
	def __init__(self):
		self._sensor_data = self._init_sensor()

	def _init_sensor(self):
		""" Returns an initialized Gyrosensor object """
		address = autopylot.config.get_gyrosensor_address()
		return autopylot.sensor.SensorData(address)

	def keep_hovering(self):
		""" tries to hold the drone as steady as possible 
		in the same position """
		gyro_data = self._sensor_data.get_gyroscope_data()
		accel_data = self._sensor_data.get_acceleration_data()

		# TODO: see my gyrosensor.md document for more info how i plan to use this figures

# vim: tabstop=4 shiftwidth=4 noexpandtab
