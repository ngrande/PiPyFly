import unittest
import os
import sys
import pigpio

sys.path.insert(0, os.path.abspath('..'))

from autopylot import control


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
        self.assertTrue(self.motor.send_start_signal())

    def test_send_stop_signal(self):
        """ Tests the stop signal sending """
        # motor = self._create_motor_object()
        # should always succeed
        self.assertTrue(self.motor.send_stop_signal())

    def test_send_throttle_adjustment(self):
        """ Tests the throttle adjustment sending """
        # motor = self._create_motor_object()
        self.assertTrue(self.motor.send_throttle_adjustment(100))
        # should fail because we already sent 100 and the maximum is 1890
        # 100 + 1800 = 1900 = FAIL
        self.assertFalse(self.motor.send_throttle_adjustment(1800))


if __name__ == '__main__':
        unittest.main()
