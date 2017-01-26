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
        self.motor = control.Motor(pi=self.pi, pin=4, start_signal=1000,
                                   stop_signal=0, min_throttle=1068,
                                   max_throttle=1890)

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

    def test_send_throttle_adjustment(self):
        """ Tests the throttle adjustment sending.
        Will perform a motor start, an normal adjustment, a too high adjustment
        and a too low adjustment. """
        self.assertTrue(self.motor.send_start_signal())
        self.assertTrue(self.motor.send_throttle_adjustment(100))
        # should fail because we already sent 100 and the maximum is 1890
        # 100 + 1800 = 1900 = FAIL
        # with self.assertRaises(Exception):
        #     self.motor.send_throttle_adjustment(800)
        # with self.assertRaises(Exception):
        #     self.motor.send_throttle_adjustment(-200)
        self.assertFalse(self.motor.send_throttle_adjustment(800))
        self.assertFalse(self.motor.send_throttle_adjustment(-200))
        # self.assertTrue(self.motor.send_throttle_adjustment(760))

    def test_send_throttle(self):
        """ Tests the throttle sending.
        Will perform a motor start, an normal throttle and three failing
        throttle values (negative value, zero and much too high) """

        self.assertTrue(self.motor.send_start_signal())
        self.assertTrue(self.motor.send_throttle(1200))
        self.assertFalse(self.motor.send_throttle(-1))
        self.assertFalse(self.motor.send_throttle(0))
        self.assertFalse(self.motor.send_throttle(99999))

    def test_decorator_check_throttle_change(self):
        """ Tests the decorator which checks the throttle change and should
        write a warning in the log file - stating that the change could
        be harmful """

        self.assertTrue(self.motor.send_start_signal())
        # from 0 to 100
        self.assertTrue(self.motor.send_throttle(1860))
        # TODO: add assert for logging
        # self.assertTrue(autopylot.logging.)
        # with self.assertLogs(autopylot.logging.getLogger(autopylot.__name__),
        # logging.WARNING):
        #     self.motor.send_throttle(1860)


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

    def test_turn_on_turn_off(self):
        """ Tests turning on and then turning off """
        self.assertTrue(self.quadcopter.turn_on())
        self.assertTrue(self.quadcopter.turn_off())

    def test_turn_off_turn_on_turn_off(self):
        """ Tests turning off, turning on and then off again """
        self.assertTrue(self.quadcopter.turn_off())
        self.assertTrue(self.quadcopter.turn_on())
        self.assertTrue(self.quadcopter.turn_off())

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
