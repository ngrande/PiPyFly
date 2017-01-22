""" Module to provide easy access to the Quadcopter.
All pins here are referenced by the BCM (Broadcom SOC channel) mapping """

import time
import pigpio
import logging
from . import config


################################################
# LIST OF TODOs                                #
################################################
# TODO: add checks if motor is started or NOT! #
#                                              #
################################################


class Motor():
    """ Class to contorl a single motor.
    There should not be a need to use this class - as it is
    already used by the Quadcopter class which will handle this """
    def __init__(self, pi, pin, start_signal, stop_signal,
                 min_throttle, max_throttle):
        if not pi:
            logging.critical("Pi = None. Unable to control the motor")
            raise Exception("Pi = None. Unable to take control over the motor")
        self.pi = pi
        self.pin = int(pin)
        self.start_signal = int(start_signal)
        self.stop_signal = int(stop_signal)
        self.min_throttle = int(min_throttle)
        self.max_throttle = int(max_throttle)
        self.current_throttle = 0
        self._started = False
        logging.info('Created new instance of {!s} class with following \
                     attributes: {!s}'.format(self.__class__.__name__,
                                              self.__dict__))

    def verify_motor_started(func):
        def wrapper(self, args):
            if not self._started:
                logging.error("Motor was not started properly before sending \
                              an event. Please verify your code and usage of \
                              the Motor class. Before throttling or simliar \
                              one should send the start signal.")
                raise Exception("Motor was not started (no start signal sent).\
                                This could lead to damage of the hardware / \
                                electronics or your environment.")
            else:
                return func(args)

    def check_throttle_change(func):
        """ Wrapper to warn the user if the throttle change is too harsh
        / fast / could damge the motors """
        def wrapper(self, args):
            before_change = self.current_throttle
            func(args)
            after_change = self.current_throttle
            total_change = abs(before_change - after_change)
            total_change_perc = total_change * 100 / (self.max_throttle -
                                                      self.min_throttle)
            if total_change_perc >= 33:
                logging.warning("Detected a change of throttle from {!s} to \
                                {!s} ({!s}%). Please verify the usage and \
                                check if this could damage your motors."
                                .format(before_change, after_change,
                                        total_change_perc))

    def is_started(self):
        return self._started

    def send_start_signal(self):
        """ Sends the start signal (initiation sequence) to the motor (pin).
        Returns True if successful otherwise False
        (also if already started). """
        if self._started:
            return False
        try:
            self.pi.set_servo_pulsewidth(self.pin, self.start_signal)
            self._started = True
            self.current_throttle = self.start_signal
            logging.info("Successfully sent start signal ({!s}) \
                         to the pin {!s}".format(self.start_signal, self.pin))
            return True
        except Exception as e:
            logging.exception("Eror while sending start signal ({!s}) \
                              to the pin {!s}".format(self.start_signal,
                                                      self.pin))
            return False

    def send_stop_signal(self):
        """ Sends the stop signal to the motor (pin). Returns True if successful
        and otherwise False. """
        try:
            self.pi.set_servo_pulsewidth(self.pin, self.stop_signal)
            self._started = False
            self.current_throttle = self.stop_signal
            logging.info("Successfully sent stop signal ({!s}) \
                         to the pin {!s}".format(self.stop_signal, self.pin))
            return True
        except Exception as e:
            logging.exception("Error while sending stop signal ({!s}) \
                              to the pin {!s}".format(self.stop_signal,
                                                      self.pin))
            return False

    @verify_motor_started
    def send_throttle_adjustment(self, throttle_add):
        """ increases / decreases the current throttle by the
        throttle_add value """
        new_total_throttle = self.current_throttle + throttle_add
        logging.info("Sending throttle adjustment of {!s} to current \
                     throttle {!s}".format(throttle_add,
                                           self.current_throttle))
        # easier and cleaner when just using the general function
        res = self.send_throttle(new_total_throttle)
        return res

    @verify_motor_started
    @check_throttle_change
    def send_throttle(self, throttle):
        """ sets the current throttle to the new value """
        if throttle < self.min_throttle:
            raise Exception("Can not set throttle ({!s}) lower than the \
                            minimum ({!s})".format(throttle,
                                                   self.min_throttle))
        elif throttle > self.max_throttle:
            raise Exception("Can not set throttle higher ({!s}) than the \
                            maximum ({!s})".format(throttle,
                                                   self.max_throttle))

        try:
            # TODO: add some checks like:
            # * throttle too high cmpared to current throttle?
            # Could hurt motors?
            # * throttle too low compared to current throttle?
            # Could hurt drone?
            self.pi.set_servo_pulsewidth(self.pin, throttle)
            current_throttle_before = self.current_throttle
            self.current_throttle = throttle
            logging.info("Successfully adjusted throttle from {!s} to {!s} \
                         on pin {!s}".format(current_throttle_before,
                                             self.current_throttle, self.pin))
            return True
        except Exception as e:
            logging.exception("Error while adjusting throttle to {!s} \
                              on pin {!s}".format(throttle, self.pin))
            return False


class Quadcopter():
    """ Class to control the quadcopter """
    def __init__(self):
        self.pi = pigpio.pi()


class Gyroscope():
    """ Class to interface the gyrosensor """
    def __init__(self, pi, pin):
        self.pin = pin
