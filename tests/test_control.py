import unittest
import os
import sys
# import logging

import pigpio
# import psutil

sys.path.insert(0, os.path.abspath('..'))

import autopylot
import autopylot.control as control


class TestControlMotor(unittest.TestCase):
	""" Class to test the motor control class """

	def setUp(self):
		self.pi = pigpio.pi()
		self.min_throttle = 1068
		self.max_throttle = 1890
		self.motor = control.Motor(pi=self.pi, pin=6, start_signal=1000,
								stop_signal=0,
								min_throttle=self.min_throttle,
								max_throttle=self.max_throttle,
								cw_rotation=True)

	def tearDown(self):
		self.pi = None
		self.motor = None

	def test_send_start_signal(self):
		""" Tests the start signal sending and if it fails when sending it
		again before stopping """
		# motor = self._create_motor_object()
		# first start should succeed
		self.assertTrue(self.motor.send_start_signal())
		# second start should not succeed because it is already started
		self.assertFalse(self.motor.send_start_signal())

	def test_send_stop_signal(self):
		""" Tests the stop signal sending """
		# motor is not yet started - should not raise Exception or anything
		# because it does not hurt to turn it off unncessarily often...
		self.assertTrue(self.motor.send_stop_signal())
		# we have to start the motor before sending stop signal...
		self.assertTrue(self.motor.send_start_signal())
		# should always succeed
		self.assertTrue(self.motor.send_stop_signal())

	# def test_send_throttle_adjustment(self):
	#     """ Tests the throttle % adjustment sending.
	#     Will perform a motor start, an normal adjustment, a too high adjustment
	#     and a too low adjustment. """
	#     self.assertTrue(self.motor.send_start_signal())
	#     self.assertTrue(self.motor.send_throttle_adjustment(10))
	#     self.assertTrue(self.motor.send_throttle_adjustment(90))
	#     self.assertFalse(self.motor.send_throttle_adjustment(1))
	#     # should fail because we already sent 100 and the maximum is 1890
	#     # 100 + 1800 = 1900 = FAIL
	#     # with self.assertRaises(Exception):
	#     #     self.motor.send_throttle_adjustment(800)
	#     # with self.assertRaises(Exception):
	#     #     self.motor.send_throttle_adjustment(-200)
	#     self.assertFalse(self.motor.send_throttle_adjustment(800))
	#     self.assertFalse(self.motor.send_throttle_adjustment(-200))
	#     self.assertTrue(self.motor.send_stop_signal())
	#     # self.assertTrue(self.motor.send_throttle_adjustment(760))

	def test_send_throttle(self):
		""" Tests the throttle % sending.
		Will perform a motor start, an normal throttle and three failing
		throttle values (negative value, zero and much too high) """

		self.assertTrue(self.motor.send_start_signal())
		self.assertTrue(self.motor.send_throttle(20))
		self.assertFalse(self.motor.send_throttle(-1))
		self.assertFalse(self.motor.send_throttle(101))
		self.assertFalse(self.motor.send_throttle(99999))
		self.assertTrue(self.motor.send_stop_signal())

	def test_decorator_check_throttle_change(self):
		""" Tests the decorator which checks the throttle change and should
		write a warning in the log file - stating that the change could
		be harmful """

		self.assertTrue(self.motor.send_start_signal())
		# from 0 to 100
		self.assertTrue(self.motor.send_throttle(100))
		# TODO: add assert for logging
		# self.assertTrue(autopylot.logging.)
		# with self.assertLogs(autopylot.logging.getLogger(autopylot.__name__),
		# logging.WARNING):
		#     self.motor.send_throttle(1860)

	def test_create_perc_to_value_dict(self):
		""" Tests the creation of the percent to value map dictionary.
		Min throttle should always be mapped to 1% and max throttle to 100% """
		min_max_throlles = [(1068, 1860), (1000, 2000), (3, 103)]

		for min_v, max_v in min_max_throlles:
			mapped_dict = self.motor._create_perc_value_map(min_v, max_v)
			self.assertTrue(mapped_dict[1] == min_v)
			self.assertTrue(mapped_dict[100] == max_v)
			self.assertFalse(mapped_dict[0] == min_v)
			self.assertTrue(len(mapped_dict) == 101)

	def test_convert_percent_to_actual_value(self):
		""" Tests if the convert percent to actual value is giving back a valid
		value in each case """
		input_too_low = -10
		input_too_high = 101
		input_correct = 33
		self.assertIs(
			self.motor._convert_percent_to_actual_value(input_too_low),
			self.motor._perc_value_map[0])
		self.assertIs(self.motor._convert_percent_to_actual_value(
			input_too_high), self.motor._perc_value_map[100])
		self.assertIs(
			self.motor._convert_percent_to_actual_value(input_correct),
			self.motor._perc_value_map[33])


class TestControlQuadcopter(unittest.TestCase):
	""" Class to test the quadcopter control class """

	def setUp(self):
		self.quadcopter = control.Quadcopter()

	def tearDown(self):
		# self.quadcopter.shutdown()
		self.quadcopter = None

	def test_turn_on(self):
		""" Tests the turn on method """
		self.assertTrue(self.quadcopter.turn_on())

	def test_turn_off(self):
		""" Tests the turn off method """
		self.assertTrue(self.quadcopter.turn_off())

	def test_is_daemon_running(self):
		""" Tests if it can detect the pigpiod daemon process running """
		self.assertTrue(self.quadcopter._is_daemon_running())

	def test_turn_on_turn_off(self):
		""" Tests turning on and then turning off """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.turn_off())

	def test_turn_off_turn_on_turn_off(self):
		""" Tests turning off, turning on and then off again """
		self.assertTrue(self.quadcopter.turn_off())
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.turn_off())

	def test_change_overall_throttle(self):
		""" Tests changing the overall throttle of the quadcopter """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(20))
		self.assertFalse(self.quadcopter.change_overall_throttle(-20))
		self.assertFalse(self.quadcopter.change_overall_throttle(-200))
		self.assertTrue(self.quadcopter.change_overall_throttle(100))
		self.assertTrue(self.quadcopter.change_overall_throttle(0))

	def test_change_yaw(self):
		""" Tests changing the yaw of the quadcopter """
		# TODO would be useful here to scan though each motor after Performing
		# a change of yaw and see if it was applied correctly
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		self.assertTrue(self.quadcopter.change_yaw(20))
		self.assertTrue(self.quadcopter.change_yaw(-20))
		self.assertTrue(self.quadcopter.change_yaw(0))
		self.assertFalse(self.quadcopter.change_yaw(101))

	def test_change_yaw__while_hover_and_control_each_motor(self):
		""" Tests changing the yaw of the quadcopter """
		# TODO would be useful here to scan though each motor after Performing
		# a change of yaw and see if it was applied correctly
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		# TODO: change yaw(100) would result in stange settings... find a solution
		self.assertTrue(self.quadcopter.change_yaw(20))

		for motor in self.quadcopter._for_each_motor():
			if motor.cw_rotation:
				self.assertIs(motor.current_throttle, 60)
			else:
				self.assertIs(motor.current_throttle, 40)

		self.assertTrue(self.quadcopter.change_yaw(0))

		for motor in self.quadcopter._for_each_motor():
			self.assertIs(motor.current_throttle, 50)

		self.assertTrue(self.quadcopter.change_yaw(100))

		for motor in self.quadcopter._for_each_motor():
			if motor.cw_rotation:
				self.assertIs(motor.current_throttle, 100)
			else:
				self.assertIs(motor.current_throttle, 0)

	def test_change_tilt_front(self):
		""" Tests changing the tilt to the front """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		self.assertTrue(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front, adjustment=20))
		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 40)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 40)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 60)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 60)
	
	def test_change_tilt_rear(self):
		""" tests changing the tilt to the rear """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		self.assertTrue(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front, adjustment=-20))
		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 60)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 60)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 40)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 40)
		
	def test_change_tilt_front_left(self):
		""" Tests changing the tilt to the front left """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))

		self.assertTrue(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front_left,
			adjustment=20))
		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 40)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 60)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 50)

	def test_change_tilt_front_right(self):
		""" Tests changing the tilt to the front right """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))

		self.assertTrue(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front_right,
			adjustment=20))
		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 40)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 60)

	def test_change_tilt_rear_left(self):
		""" Tests changing the tilt to the rear left """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))

		self.assertTrue(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front_right,
			adjustment=-20))
		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 60)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 40)

	def test_change_tilt_fail(self):
		""" Tests changing the tilt to an invalid value - expected to fail """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))

		self.assertFalse(self.quadcopter.change_tilt(
			side=self.quadcopter.TiltSide.front_right,
			adjustment=-200))

	def test_hover(self):
		""" Tests hover """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		self.assertTrue(self.quadcopter.change_yaw(20))
		self.assertTrue(self.quadcopter.change_tilt(
			self.quadcopter.TiltSide.left, -30))
		self.assertTrue(self.quadcopter.hover())

		self.assertIs(self.quadcopter._motor_front_left.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_front_right.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_rear_right.current_throttle, 50)
		self.assertIs(self.quadcopter._motor_rear_left.current_throttle, 50)

	def test_request_total_throttle(self):
		""" Test requesting total throttle """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(100))
		self.assertEqual(self.quadcopter.request_total_throttle(), 400)

	def test_request_throttle(self):
		""" Test requesting throttle of each individual motor """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(50))
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_left), 50)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_left), 50)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_right), 50)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_right), 50)

		self.assertTrue(self.quadcopter.change_tilt(self.quadcopter.TiltSide.front, 50))
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_left), 25)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_left), 75)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_right), 25)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_right), 75)


	def test_tilt_edge_case(self):
		""" test tilt edge case - when already at 100 throttle """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(100))
		self.assertFalse(self.quadcopter.change_tilt(self.quadcopter.TiltSide.front, 50))
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_left), 50)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_left), 100)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.front_right), 50)
		self.assertIs(self.quadcopter.request_throttle(self.quadcopter.MotorSide.rear_right), 100)

	def test_yaw_edge_case(self):
		""" test yaw edge case - when already at 100 throttle """
		self.assertTrue(self.quadcopter.turn_on())
		self.assertTrue(self.quadcopter.change_overall_throttle(100))
		self.assertFalse(self.quadcopter.change_yaw(10))

		for motor in self.quadcopter._for_each_motor():
			if motor.cw_rotation:
				self.assertIs(motor.current_throttle, 100)
			else:
				self.assertIs(motor.current_throttle, 90)

	
	# ########################################################################
	# def test_auto_daemon_spawn(self):
	#     """ Tests if the Quadcopter automatically spawns the pigpiod daemon
	#     process """
	#     # first kill the pigpiod if exists
	#     daemon_name = "pigpiod"
	#     daemon_pid = None
	#     for pid in psutil.pids():
	#         if psutil.Process(pid).name() == daemon_name:
	#             daemon_pid = pid
	#             break
	#     os.kill(daemon_pid, 15)
	#     quad = control.Quadcopter()
	#     daemon_running = any([psutil.Process(pid).name() == daemon_name
	#                           for pid in psutil.pids()])
	#     self.assertTrue(daemon_running)
	# ########################################################################


if __name__ == '__main__':
	unittest.main()

# vim: tabstop=4 shiftwidth=4 noexpandtab
