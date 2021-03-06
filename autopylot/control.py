""" Low level module to provide (easy) access to the Quadcopter.
All pins here are referenced by the BCM (Broadcom SOC channel) mapping.
In this module you can change the throttle of the motors as you wish without
any checks that prevent you from doing so - so be careful."""

# standard modules
import os
import time
import logging
import subprocess
import enum
import functools

# pip installed modules
import psutil
# import mpu6050
import pigpio

# my modules
import autopylot.config

###############################################################################
# PRINCIPLE OF BEHAVIOR
###############################################################################
# The user should only be able to send suggestions to the drone.
# The drone should always verify this and check if it is safe to do so. If yes
# it could proceed with this action and if not it should self decide what to
# do in the current situation.
# ---------------------------------------------
# Always keep safety in mind and never risk a move.
# Always expect components to fail
# Expect the unexpected
# Priority Nr. 1: Be responsive and stay alive
###############################################################################

# *****************
# * READ FIRST
# *****************
# This is the LOW LEVEL module which gives you full control over the quadcopter
# and does not interfere with what you wish to do. You can send the quad to heaven or death
# however you please to do. Use a higher level module to have a secure access of control.
#

class Motor():
	""" Class to control a single motor.
	There should not be a need to use this class - as it is
	already used by the Quadcopter class which will handle this """

	def __init__(self, pi, pin, cw_rotation, start_signal, stop_signal,
				min_throttle, max_throttle):
		if not pi:
			raise Exception("Pi = None. Unable to take control over the motor")
		self.pi = pi
		self.pin = int(pin)
		self.cw_rotation = bool(cw_rotation)
		self.start_signal = int(start_signal)
		self.stop_signal = int(stop_signal)
		self.min_throttle = int(min_throttle)  # => 1% throttle
		self.max_throttle = int(max_throttle)  # => 100% throttle
		self.current_throttle = 0  # in percent % (1% => min_throttle)
		self._started = False
		self._perc_value_map = self._create_perc_value_map(self.min_throttle,
															self.max_throttle)
		# the callback return object - do not change this - it is private!
		self._gpio_callback = None
		logging.info("Created new instance of {!s} class with following "
					"attributes: {!s}".format(self.__class__.__name__,
											self.__dict__))

	###########################################################################
	# Decorator functions
	###########################################################################
	def verify_motor_started(func):
		""" Wrapper to verify that the motor is started - should be used
		on functions / methods which send signals to the ESC """

		def wrapper(self, *args):
			if not self._started:
				raise Exception("Motor was not started (no start signal sent)."
								" This could lead to damage of the hardware / "
								"electronics or your environment.")
			return func(self, *args)
		return wrapper

	def check_throttle_change(func):
		""" Wrapper to warn the user if the throttle change is too harsh
		/ fast / could damage the motors """

		def wrapper(self, *args):
			before_change = self.current_throttle
			res = func(self, *args)
			after_change = self.current_throttle
			total_change = abs(before_change - after_change)
			# total_change_perc = total_change * 100 / before_change
			if total_change >= 33:
				logging.warning("Detected a change of throttle from {!s} to "
								"{!s} ({!s}%). Please verify the usage"
								" and check if this could damage your motors."
								.format(before_change, after_change,
										total_change))
			return res
		return wrapper

	###########################################################################
	# END
	###########################################################################

	def _register_gpio_watchdog(self):
		""" Registers a watchdog and callback function to the gpio pin.
		This is used to check if the communication is stable """
		if self._gpio_callback is not None:
			return

		def callback_func(gpio, level, tick):
			""" Callback for the gpio pin of the Motor. At the moment only
			used to log timeout signals from the pigpio watchdog """
			if level == pigpio.TIMEOUT:
				logging.warning("Timeout event triggered from watchdog on "
								"pin: {!s} (tick: {!s}). Check the motor "
								"responsiveness or adjust the watchdog."
								.format(gpio, tick))

		self._gpio_callback = self.pi.callback(self.pin, pigpio.EITHER_EDGE,
											callback_func)

		#######################################################################
		# set a watchdog to the pin - the servo pulsewidth should be sent
		# periodically - so the watchdog would only trigger when there
		# is an unexpected behavior...
		#
		# set watchdog to 10ms (because we need full control over the motor)
		# #####################################################################
		wd_timeout_ms = 100
		self.pi.set_watchdog(self.pin, wd_timeout_ms)
		logging.info("Activated a watchdog (timeout: {!s}ms) and callback for "
					"pin: {!s}".format(wd_timeout_ms, self.pin))

	def _unregister_gpio_watchdog(self):
		""" Deactivate the watchdog and callback for the motor pin """
		if self._gpio_callback:
			self._gpio_callback.cancel()
			self._gpio_callback = None

		self.pi.set_watchdog(self.pin, 0)
		logging.info("Deactivated watchdog and callback for pin: {!s}"
					.format(self.pin))

	def _create_perc_value_map(self, min_throttle, max_throttle):
		""" Maps the min and max throttle values into a map of percentage
		values - this saves a lot of computations later.
		min throttle => 1% and max throttle => 100%. """
		perc_to_value_dict = {}
		step = (max_throttle - min_throttle) / 99
		one_perc = min_throttle - step  # to let min throttle be 1%
		for perc in range(0, 101):  # the map should go from 1 to 100
			perc_to_value_dict[perc] = int(one_perc + (step * perc))

		# assert that dict is 101 long because we have 101 steps
		# 0 = one stop under the min throttle
		# 1 = min throttle
		# 100 = max throttle
		# sum: 101 values
		assert len(perc_to_value_dict) == 100 + 1, "map is out of bounds"

		return perc_to_value_dict

	def _convert_percent_to_actual_value(self, percent_val):
		""" Converts the percentage (throttle) value to the actual value.
		1% => min throttle and 100% => max throttle """
		#######################################################################
		# 1% => Min throttle
		# 100% => Max Throttle
		# these values are pre calculated (and stored in a dict)
		# for faster computation
		#######################################################################
		normalized_value = percent_val
		if percent_val not in range(0, 101):
			logging.error("percent_val ({!s}) was not within the valid "
						"range from 1 to 100.".format(percent_val))
			if percent_val < 0:
				normalized_value = 0
			elif percent_val > 100:
				normalized_value = 100
			logging.warning("changed the percent_val input from {!s} to a "
							"valid {!s}".format(percent_val, normalized_value))
		actual_value = self._perc_value_map[normalized_value]
		return actual_value

	def send_start_signal(self):
		""" Sends the start signal (initiation sequence) to the motor (pin).
		Returns True if successful otherwise False
		(also if already started). """
		if self._started:
			return False
		try:
			self.pi.set_servo_pulsewidth(self.pin, self.start_signal)
			self._started = True
			self._register_gpio_watchdog()
			self.current_throttle = 0
			logging.info("Successfully sent start signal ({!s}) "
						"to the pin {!s}".format(self.start_signal, self.pin))
			return True
		except Exception as e:
			logging.exception("Eror while sending start signal ({!s}) "
							"to the pin {!s}".format(self.start_signal, self.pin))
			return False

	def send_stop_signal(self):
		""" Sends the stop signal to the motor (pin). Returns True if successful
		and otherwise False. """
		if not self._started:
			logging.warning("Motor on pin {!s} was not started before "
							"receiving stop signal...".format(self.pin))

		try:
			self.pi.set_servo_pulsewidth(self.pin, self.stop_signal)
			self._started = False
			self._unregister_gpio_watchdog()
			self.current_throttle = 0
			logging.info("Successfully sent stop signal ({!s}) "
						"to the pin {!s}".format(self.stop_signal, self.pin))
			return True
		except Exception as e:
			logging.exception("Error while sending stop signal ({!s}) "
							"to the pin {!s}".format(self.stop_signal, self.pin))
			return False

	# @verify_motor_started
	# def send_throttle_adjustment(self, throttle_add):
	#     """ increases / decreases the current throttle by the
	#     throttle_add value (in percent %) """
	#     new_total_throttle = int(self.current_throttle + throttle_add)
	#     logging.info("Sending throttle adjustment of {!s}% to current "
	#                 "throttle {!s}%".format(throttle_add,
	#                                         self.current_throttle))
	#     # easier and cleaner when just using the general function
	#     res = self.send_throttle(new_total_throttle)
	#     return res

	@verify_motor_started
	@check_throttle_change
	def send_throttle(self, throttle):
		""" sets the current throttle (in percent %) to the new value """
		throttle = int(throttle)
		# TODO: think about not preventing a change below or above the 0 - to 100
		# because how does the user later decide how much throttle is left?
		# and we have a normalization in the _convert_percent_to_actual_value method
		if throttle < 0:
			text_error_too_low = "Can not set throttle ({!s}%) lower than " \
				"0%".format(throttle, self.min_throttle)
			logging.error(text_error_too_low)
			# do not throw an exception we want to keep the motor alive
			# raise Exception(text_error_too_low)
			return False
		elif throttle > 100:
			text_error_too_high = "Can not set throttle higher ({!s}%) than "\
				"100%".format(throttle, self.max_throttle)
			logging.error(text_error_too_high)
			# do not throw an exception we want to keep the motor alive
			# raise Exception(text_error_too_high)
			return False

		try:
			actual_throttle_value = self._convert_percent_to_actual_value(
				throttle)
			self.pi.set_servo_pulsewidth(self.pin, actual_throttle_value)
			current_throttle_before = self.current_throttle
			self.current_throttle = throttle
			logging.info("Successfully adjusted throttle from {!s}% to {!s}% "
						"on pin {!s}".format(current_throttle_before,
											self.current_throttle, self.pin))
			return True
		except Exception as e:
			logging.exception("Error while adjusting throttle to {!s}% "
							"on pin {!s}".format(throttle, self.pin))
			return False


class Quadcopter():
	""" Class to control the quadcopter """

	class TiltSide(enum.Enum):
		""" Enum to indicate the side which to tilt """
		front = 1
		left = 2
		front_left = 3
		front_right = 4

	class MotorSide(enum.Enum):
		""" Enum to indicate the motor """
		front_right = 1
		rear_right = 2
		rear_left = 3
		front_left = 4

	def __init__(self):
		pigpiod_running = self._is_daemon_running()
		if not pigpiod_running:
			# self._start_pigpio_daeomon()
			raise Exception("pigpiod daemon did not start properly. "
							"Check permissions and / or if installed properly")
		self.pi = pigpio.pi()
		# TODO: call self.pi.stop() in the end...
		if not self.pi.connected:
			# no connection to the GPIO pins possible...
			raise Exception("Unable to connect to the GPIO pins. Is the daemon running?")

		self.turned_on = False
		self.min_throttle = autopylot.config.get_min_throttle()
		self.max_throttle = autopylot.config.get_max_throttle()
		# not sure about this value? Why 1000? Is this not motor specific?
		# Shouldn't it be configurable?
		self.start_signal = 1000
		self.stop_signal = 0
		self._motor_front_left = self._init_motor(
			autopylot.config.get_motor_front_left_pin(),
			autopylot.config.get_motor_front_left_rotation_is_cw())
		self._motor_front_right = self._init_motor(
			autopylot.config.get_motor_front_right_pin(),
			autopylot.config.get_motor_front_right_rotation_is_cw())
		self._motor_rear_left = self._init_motor(
			autopylot.config.get_motor_rear_left_pin(),
			autopylot.config.get_motor_rear_left_rotation_is_cw())
		self._motor_rear_right = self._init_motor(
			autopylot.config.get_motor_rear_right_pin(),
			autopylot.config.get_motor_rear_right_rotation_is_cw())

	def _init_motor(self, pin, cw_rotation):
		""" Returns an initialized Motor object """
		return Motor(self.pi, pin, cw_rotation, self.start_signal,
					self.stop_signal, self.min_throttle, self.max_throttle)

	def _check_motor_rotations(self):
		""" Checks if the quadcopter will be able to stay still (rotation should
		be cw + ccw + cw + ccw) """
		if (self._motor_front_left.cw_rotation ==
				self._motor_front_right.cw_rotation):
			logging.critical("The two front motors should not be rotating "
							"in the same direction (cw or ccw)")
			return False
		if (self._motor_rear_left.cw_rotation ==
				self._motor_rear_right.cw_rotation):
			logging.critical("The two rear motors should not be rotating "
							"in the same direction (cw or ccw)")
			return False
		if (self._motor_front_left.cw_rotation ==
				self._motor_rear_left.cw_rotation):
			logging.critical("The two left motors (front and rear) should not "
							"be rotating in the same direction (cw or ccw)")
			return False
		if (self._motor_front_right.cw_rotation ==
				self._motor_rear_right.cw_rotation):
			logging.critical("The two right motors (front and rear) should "
							"not be rotating in the same direction "
							"(cw or ccw)")
			return False

	def _is_daemon_running(self):
		""" Searches for the pigpiod daemon process. Returns True if found
		else False. """
		daemon_name = 'pigpiod'
		daemon_running = any([psutil.Process(pid).name() == daemon_name
							for pid in psutil.pids()])
		return daemon_running

	# this method is not used in the moment...
	def _start_pigpio_daeomon(self):
		""" Checks if the pigpiod daemon is already running and if not it
		will be started. Returns True if the daemon was started (successfully)
		or was already running. Otherwise False """
		daemon_name = 'pigpiod'

		if not self._is_daemon_running():
			# start pigpiod
			sample_rate = autopylot.config.get_pigpiod_sample_rate()
			subproc_command = [daemon_name, '-s', str(sample_rate)]
			try:
				subprocess.Popen(subproc_command)
			except Exception as e:
				logging.exception("Exception occurred while starting the "
								"pigpio daemon ({!s}): {!s}"
								.format(daemon_name, e))
				return False
			logging.info("Started {!s} via subprocess ({!s})."
						.format(daemon_name, subproc_command))
		else:
			logging.info("{!s} was already running. No further action "
						"required. This means we did not set the sample "
						"rate from the .ini configuration."
						.format(daemon_name))
		return self._is_daemon_running()

	def _for_each_motor(self):
		""" Returns a list of all motors where you can iterate over """
		return [self._motor_rear_left, self._motor_rear_right,
				self._motor_front_left, self._motor_front_right]

	def turn_off(self):
		""" Sends stop signal to each motor and stops the pigpio.pi object """
		overall_success = True
		try:
			for motor in self._for_each_motor():
				success = motor.send_stop_signal()
				if not success:
					logging.critical("Unable to stop motor: {!s}"
									.format(motor.__dict__))
					overall_success = False
			# self.pi.stop()
			self.turned_on = False
		except Exception as e:
			logging.exception("Exception occurred while sending the start "
							"signal to the motors: {!s}".format(e))
			overall_success = False
		return overall_success

	def turn_on(self):
		""" Sends start signal to each motor """
		overall_success = True
		try:
			for motor in self._for_each_motor():
				success = motor.send_start_signal()
				if not success:
					logging.critical("Unable to start motor: {!s}"
									.format(motor.__dict__))
					overall_success = False
			self.turned_on = True
		except Exception as e:
			logging.exception("Exception occurred while sending the start "
							"signal to the motors: {!s}".format(e))
			overall_success = False
		return overall_success

	def change_overall_throttle(self, throttle):
		""" changes the overall throttle. Valid value is
		from 0 to 100 """
		throttle = int(throttle)
		overall_success = True
		try:
			for motor in self._for_each_motor():
				success = motor.send_throttle(throttle)
				if not success:
					logging.critical("Unable to send throttle (%) adjustment "
									"({!s}) to motor: {!s}"
									.format(throttle, motor.__dict__))
					overall_success = False
		except Exception as e:
			logging.exception("Exception occured while sending throttle "
							"adjustment to the motors: {!s}".format(e))
			overall_success = False
		return overall_success


	def request_total_throttle(self):
		""" return the total throttle (all throttle values combined) """
		total_throttle = 0
		for motor in self._for_each_motor():
			total_throttle += motor.current_throttle
		return total_throttle


	def request_throttle(self, motor_side):
		""" return the throttle value of the motor """
		if motor_side is self.MotorSide.front_left:
			return self._motor_front_left.current_throttle
		elif motor_side is self.MotorSide.front_right:
			return self._motor_front_right.current_throttle
		elif motor_side is self.MotorSide.rear_right:
			return self._motor_rear_right.current_throttle
		elif motor_side is self.MotorSide.rear_left:
			return self._motor_rear_left.current_throttle


	def hover(self):
		""" Reads the current throttle of each motor and sets them to an equal
		level so the quadcopter should hover """
		overall_success = True
		try:
			total_throttle = self.request_total_throttle()

			throttle_foreach = int(total_throttle / 4)
			for motor in self._for_each_motor():
				success = motor.send_throttle(throttle_foreach)
				if not success:
					logging.critical("Unable to send (absolute %) throttle "
									"({!s}) to motor: {!s}"
									.format(throttle_foreach, motor.__dict__))
					overall_success = False

			if overall_success:
				assert total_throttle == self.request_total_throttle(), "Total throttle should always stay consistent"
		except Exception as e:
			logging.exception("Exception occurred while trying to bring the "
							"motors on one level to hover: {!s}".format(e))
			overall_success = False

		return overall_success

	def change_yaw(self, absolute_yaw):
		""" Change the yaw - valid values are from -100 to 100 where 100 is thehighest possible yawing.
		If the value is positive it will yaw clockwise and otherwise
		counterclockwise. """
		# TODO
		# Edge cases:
		# Motor could already be at 100% throttle
		# NOTE: For the moment we can ignore the edge case when one or more
		# motors are already at 100% throttle... the yaw will still work but
		# not as fast or with a bit of altitude lose
		# Change each motor independently (because it could be tilted)
		absolute_yaw = int(absolute_yaw)
		if absolute_yaw < -100 or absolute_yaw > 100:
			logging.error("absolute_yaw exceeds +/- 100% ({!s})"
						.format(absolute_yaw))
			return False

		overall_success = True
		try:
			total_throttle = self.request_total_throttle()
			base_throttle = int(total_throttle / 4)
			factor = int(base_throttle / 100 * absolute_yaw)
			
			for motor in self._for_each_motor():
				new_throttle = None
				if motor.cw_rotation:
					new_throttle = base_throttle + factor
				else:
					new_throttle = base_throttle - factor

				overall_success = motor.send_throttle(new_throttle)

			if overall_success:
				assert total_throttle == self.request_total_throttle(), "Total throttle should always stay consistent"
		except Exception as e:
			overall_success = False
			logging.exception("Exception occured while sending throttle "
							"adjustment to motors to perform yaw: {!s}"
							.format(e))
			return False
		return overall_success

	def change_tilt(self, side, adjustment):
		""" Change the tilt to the given side (front, left, frontleft,
		frontright) - to use the opposite just use a negative value.
		Valid values for adjustment: -100 to +100 (100 is maximum tilt).
		I.e. you want to change tilt to rear you have to send: side=front
		and a negative adjustment value """
		# 100% tilt => one side is on full speed - other side is on zero speed
		adjustment = int(adjustment)
		overall_success = True
		try:
			total_throttle = self.request_total_throttle()
			base_throttle = int(total_throttle / 4)
			factor = int(base_throttle / 100 * adjustment)

			if side is self.TiltSide.front:
				overall_success = self._motor_front_right.send_throttle(base_throttle - factor)
				overall_success = self._motor_front_left.send_throttle(base_throttle - factor)
				overall_success = self._motor_rear_right.send_throttle(base_throttle + factor)
				overall_success = self._motor_rear_left.send_throttle(base_throttle + factor)

			elif side is self.TiltSide.front_left:
				overall_success = self._motor_front_right.send_throttle(base_throttle)
				overall_success = self._motor_front_left.send_throttle(base_throttle - factor)
				overall_success = self._motor_rear_right.send_throttle(base_throttle + factor)
				overall_success = self._motor_rear_left.send_throttle(base_throttle)

			elif side is self.TiltSide.front_right:
				overall_success = self._motor_front_right.send_throttle(base_throttle - factor)
				overall_success = self._motor_front_left.send_throttle(base_throttle)
				overall_success = self._motor_rear_right.send_throttle(base_throttle)
				overall_success = self._motor_rear_left.send_throttle(base_throttle + factor)
			elif side is self.TiltSide.left:
				overall_success = self._motor_front_right.send_throttle(base_throttle + factor)
				overall_success = self._motor_front_left.send_throttle(base_throttle - factor)
				overall_success = self._motor_rear_right.send_throttle(base_throttle + factor)
				overall_success = self._motor_rear_left.send_throttle(base_throttle - factor)
	

			if overall_success:
				assert total_throttle == self.request_total_throttle(), "Total throttle should always stay consistent"
		except Exception as e:
			logging.exception("Exception occured while changing tilt: {!s}"
							.format(e))
			overall_success = False
		return overall_success

# vim: tabstop=4 shiftwidth=4 noexpandtab
