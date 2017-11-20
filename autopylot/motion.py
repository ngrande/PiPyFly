""" module for motion tracking """

import time
import threading

import autopylot.sensor
import autopylot.config

# Formula
#--------------------------------
# Distance:
#    velocity = sum(acceleration)
#    distance = sum(velocity)

# Angular change:
#    tilt = sum(rotation) 

SAMPLE_COUNT = 1000

class MotionTracker():
	""" 3D Motion Tracking """
	def __init__(self):
		address = autopylot.config.get_gyrosensor_address()
		self._sensor = autopylot.sensor.SensorData(address)
		self._tilt =		{'x': 0, 'y': 0, 'z': 0}
		self._velocity =	{'x': 0, 'y': 0, 'z': 0}
		self._distance =	{'x': 0, 'y': 0, 'z': 0}

		self._accel_samples = []
		self._rotation_samples = []
		self._accel_offset = {'x': 0, 'y': 0, 'z': 0}
		self._rotation_offset = {'x': 0, 'y': 0, 'z': 0}
		self._first_sampling = True

		loop_thread = threading.Thread(target=self._loop)
		loop_thread.start()

	def get_distance(self):
		""" distance (as tuple - x,y,z) in unknown unit """
		return self._distance

	def get_tilt(self):
		""" tilt (as tuple - x,y,z) in unknown unit """
		return self._tilt

	def _avg(self, samples):
		offset = {'x': 0, 'y': 0, 'z': 0}
		for sample in samples:
			offset['x'] += sample['x']
			offset['y'] += sample['y']
			offset['z'] += sample['z']

		offset['x'] = offset['x'] / len(samples)
		offset['y'] = offset['y'] / len(samples)
		offset['z'] = offset['z'] / len(samples)
		return offset

	def _sample(self, accel, rotation):
		self._accel_samples.append(accel)
		self._rotation_samples.append(rotation)

		if len(self._accel_samples) >= SAMPLE_COUNT and len(self._rotation_samples) >= SAMPLE_COUNT:
			self._accel_offset = self._avg(self._accel_samples)
			self._rotation_offset = self._avg(self._rotation_samples)

			self._first_sampling = False
			self._accel_samples = []
			self._rotation_samples = []

	def _calc_distance(self, accel):
		self._velocity['x'] += (accel['x'] - self._accel_offset['x'])
		self._velocity['y'] += (accel['y'] - self._accel_offset['y'])
		self._velocity['z'] += (accel['z'] - self._accel_offset['z'])
		self._distance['x'] += self._velocity['x']
		self._distance['y'] += self._velocity['y']
		self._distance['z'] += self._velocity['z']

	def _calc_tilt(self, rotation):
		self._tilt['x'] += (rotation['x'] - self._rotation_offset['x'])
		self._tilt['y'] += (rotation['y'] - self._rotation_offset['y'])
		self._tilt['z'] += (rotation['z'] - self._rotation_offset['z'])

	def _loop(self):
		""" loop to sample the gyro sensor data continuously.
		The MPU-6050 currently used can sample at 1kHz so we
		will sample at 1ms """
		while True:
			accel = self._sensor.get_acceleration_data()
			print("REAL ACCEL: {!s}".format(accel))
			rotation = self._sensor.get_gyroscope_data()
			print("REAL ROTATION: {!s}".format(rotation))

			if self._first_sampling:
				self._sample(accel, rotation)
			else:
				self._calc_distance(accel)
				self._calc_tilt(rotation)

			time.sleep(0.001)



# vim: tabstop=4 shiftwidth=4 noexpandtab
