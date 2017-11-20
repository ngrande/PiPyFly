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

SAMPLE_COUNT = 100

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
		self._first_sampling = True

		self._accel_before = None
		self._rotation_before = None

		self._accel_dead_zone = (0,0)
		self._rotation_dead_zone = (0,0)

		self._filtered_rotation_before = {'x': 0, 'y': 0, 'z': 0}
		self._filtered_accel_before = {'x': 0, 'y': 0, 'z': 0}
		
		loop_thread = threading.Thread(target=self._loop)
		loop_thread.start()

	def get_distance(self):
		""" distance (as tuple - x,y,z) in unknown unit """
		return self._distance

	def get_tilt(self):
		""" tilt (as tuple - x,y,z) in unknown unit """
		return self._tilt

   #  def _avg(self, samples):
   #      offset = {'x': 0, 'y': 0, 'z': 0}
   #      for sample in samples:
   #          offset['x'] += sample['x']
   #          offset['y'] += sample['y']
   #          offset['z'] += sample['z']

   #      offset['x'] = offset['x'] / len(samples)
   #      offset['y'] = offset['y'] / len(samples)
   #      offset['z'] = offset['z'] / len(samples)
   #      return offset

	def _setup_dead_zone_filter(self, samples):
		min_dict = {	'x': samples[0]['x'], 
						'y': samples[0]['y'],
						'z': samples[0]['z']
					}
		max_dict = {	'x': samples[0]['x'], 
						'y': samples[0]['y'],
						'z': samples[0]['z']
					}


		dead_zone = [min_dict, max_dict]
		x_values = []
		y_values = []
		z_values = []
		for sample in samples:
			x_values.append(sample['x'])
			y_values.append(sample['y'])
			z_values.append(sample['z'])

		def add_blur(value):
			if value < 0:
				return value - (value * 0.2)
			else:
				return value + (value * 0.2)

		def sub_blur(value):
			if value < 0:
				return value + (value * 0.2)
			else:
				return value - (value * 0.2)
			

		min_dict['x'] = sub_blur(min(x_values))
		min_dict['y'] = sub_blur(min(y_values))
		min_dict['z'] = sub_blur(min(z_values))

		max_dict['x'] = add_blur(max(x_values))
		max_dict['y'] = add_blur(max(y_values))
		max_dict['z'] = add_blur(max(z_values))

		return dead_zone


	def _sample(self, accel, rotation):
		self._accel_samples.append(accel)
		self._rotation_samples.append(rotation)

		if len(self._accel_samples) >= SAMPLE_COUNT and len(self._rotation_samples) >= SAMPLE_COUNT:
			self._accel_dead_zone = self._setup_dead_zone_filter(self._accel_samples)
			self._rotation_dead_zone = self._setup_dead_zone_filter(self._rotation_samples)

			self._first_sampling = False
			self._accel_samples = []
			self._rotation_samples = []

	def _dead_zone_filter(self, value, dead_zone):
		if value['x'] >= dead_zone[0]['x'] and value['x'] <= dead_zone[1]['x']:
			value['x'] = 0
		if value['y'] >= dead_zone[0]['y'] and value['y'] <= dead_zone[1]['y']:
			value['y'] = 0
		if value['z'] >= dead_zone[0]['z'] and value['z'] <= dead_zone[1]['z']:
			value['z'] = 0

	def _anomaly_filter(self, value, compare):
		""" filter out anomalies - when there is a value that is
		not 0 but not followed or preceded by another non 0 value """
		filtered_value = {'x': 0, 'y': 0, 'z': 0}
		if value['x'] != 0 and compare['x'] != 0:
			filtered_value['x'] = value['x']
		if value['y'] != 0 and compare['y'] != 0:
			filtered_value['y'] = value['y']
		if value['z'] != 0 and compare['z'] != 0:
			filtered_value['z'] = value['z']

		compare['x'] = value['x']
		compare['y'] = value['y']
		compare['z'] = value['z']

	def _calc_distance(self, accel):
		self._dead_zone_filter(accel, self._accel_dead_zone)
		self._anomaly_filter(accel, self._filtered_accel_before)

		self._accel_before = accel
		self._velocity['x'] += accel['x']
		self._velocity['y'] += accel['y']
		self._velocity['z'] += accel['z']
		self._distance['x'] += self._velocity['x']
		self._distance['y'] += self._velocity['y']
		self._distance['z'] += self._velocity['z']

	def _calc_tilt(self, rotation):
		self._dead_zone_filter(rotation, self._rotation_dead_zone)
		self._anomaly_filter(rotation, self._filtered_rotation_before)

		print("VALUE: ", rotation)
		self._rotation_before = rotation
		self._tilt['x'] += rotation['x']
		self._tilt['y'] += rotation['y']
		self._tilt['z'] += rotation['z']

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
		# I THINK I KNOW HOW TO SOLVE MY PROBLEM
		# WE NEED TO CLEAR THE BUFFER OF THE MPU6050
		# AFTER EACH READ




# vim: tabstop=4 shiftwidth=4 noexpandtab
