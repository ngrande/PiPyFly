""" Module to provide easy access to the Quadcopter.
All pins here are referenced by the BCM (Broadcom SOC channel) mapping """

# standard modules
import os
import time
import logging
import subprocess

# pip installed modules
import psutil
import mpu6050
import pigpio

# my modules
from . import config


################################################
# LIST OF TODOs                                #
################################################
# TODO implement controls (like changing tilt, or yaw)
# TODO add a worst case scenario handling for example if the gyro sensor
# fails in mid fly... or one / several motors stop responding.
################################################


class Motor():
    """ Class to contorl a single motor.
    There should not be a need to use this class - as it is
    already used by the Quadcopter class which will handle this """

    def __init__(self, pi, pin, start_signal, stop_signal,
                 min_throttle, max_throttle):
        if not pi:
            logging.error("Pi = None. Unable to control the motor")
            raise Exception("Pi = None. Unable to take control over the motor")
        self.pi = pi
        self.pin = int(pin)
        self.start_signal = int(start_signal)
        self.stop_signal = int(stop_signal)
        self.min_throttle = int(min_throttle)
        self.max_throttle = int(max_throttle)
        self.current_throttle = 0
        self._started = False
        # the callback return object - do not change this - it is private!
        self._gpio_callback = None
        logging.info("Created new instance of {!s} class with following "
                     "attributes: {!s}".format(self.__class__.__name__,
                                               self.__dict__))

    def verify_motor_started(func):
        def wrapper(self, *args):
            if not self._started:
                logging.error("Motor was not started properly before sending "
                              "an event. Please verify your code and usage of "
                              "the Motor class. Before throttling or simliar "
                              "one should send the start signal.")
                raise Exception("Motor was not started (no start signal sent)."
                                " This could lead to damage of the hardware / "
                                "electronics or your environment.")
            return func(self, *args)
        return wrapper

    def check_throttle_change(func):
        """ Wrapper to warn the user if the throttle change is too harsh
        / fast / could damge the motors """

        def wrapper(self, *args):
            before_change = self.current_throttle
            res = func(self, *args)
            after_change = self.current_throttle
            total_change = abs(before_change - after_change)
            total_change_perc = total_change * 100 / before_change
            if total_change_perc >= 33:
                logging.warning("Detected a change of throttle from {!s} to "
                                "{!s} ({!s} -> {!s}%). Please verify the usage"
                                " and check if this could damage your motors."
                                .format(before_change, after_change,
                                        total_change, total_change_perc))
            return res
        return wrapper

    def _register_gpio_watchdog(self):
        """ Registers a watchdog and callback function to the gpio pin.
        This is used to check if the communication is stable """
        if self._gpio_callback is not None:
            return

        def callback_func(gpio, level, tick):
            if level == pigpio.TIMEOUT:
                logging.warning("Timeout event triggered from watchdog on "
                                "pin: {!s} (tick: {!s}). Check the motor "
                                "responsivness or adjust the watchdog."
                                .format(gpio, tick))

        self._gpio_callback = self.pi.callback(self.pin, pigpio.EITHER_EDGE,
                                               callback_func)

        # *******************************************************
        # set a watchdog to the pin - the servo pulsewidth should be sent
        # periodically - so the watchdog would only trigger when there
        # is an unexpected behavior...
        # *******************************************************

        # set watchdog to 5ms (because we need full control over the motor)
        wd_timeout_ms = 5
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
            self._register_gpio_watchdog()
            self.current_throttle = self.start_signal
            logging.info("Successfully sent start signal ({!s}) "
                         "to the pin {!s}".format(self.start_signal, self.pin))
            return True
        except Exception as e:
            logging.exception("Eror while sending start signal ({!s}) "
                              "to the pin {!s}".format(self.start_signal,
                                                       self.pin))
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
            self.current_throttle = self.stop_signal
            logging.info("Successfully sent stop signal ({!s}) "
                         "to the pin {!s}".format(self.stop_signal, self.pin))
            return True
        except Exception as e:
            logging.exception("Error while sending stop signal ({!s}) "
                              "to the pin {!s}".format(self.stop_signal,
                                                       self.pin))
            return False

    @verify_motor_started
    def send_throttle_adjustment(self, throttle_add):
        """ increases / decreases the current throttle by the
        throttle_add value """
        new_total_throttle = self.current_throttle + throttle_add
        logging.info("Sending throttle adjustment of {!s} to current "
                     "throttle {!s}".format(throttle_add,
                                            self.current_throttle))
        # easier and cleaner when just using the general function
        res = self.send_throttle(new_total_throttle)
        return res

    @verify_motor_started
    @check_throttle_change
    def send_throttle(self, throttle):
        """ sets the current throttle to the new value """
        if throttle < self.min_throttle:
            text_error_too_low = "Can not set throttle ({!s}) lower than the "\
                "minimum ({!s})".format(throttle, self.min_throttle)
            logging.error(text_error_too_low)
            # do not throw an exception we want to keep the motor alive
            # raise Exception(text_error_too_low)
            return False
        elif throttle > self.max_throttle:
            text_error_too_high = "Can not set throttle higher ({!s}) than "\
                "the maximum ({!s})".format(throttle, self.max_throttle)
            logging.error(text_error_too_high)
            # do not throw an exception we want to keep the motor alive
            # raise Exception(text_error_too_high)
            return False

        try:
            # TODO: add some checks like:
            # * throttle too high cmpared to current throttle?
            # Could hurt motors?
            # * throttle too low compared to current throttle?
            # Could hurt drone?
            self.pi.set_servo_pulsewidth(self.pin, throttle)
            current_throttle_before = self.current_throttle
            self.current_throttle = throttle
            logging.info("Successfully adjusted throttle from {!s} to {!s} "
                         "on pin {!s}".format(current_throttle_before,
                                              self.current_throttle, self.pin))
            return True
        except Exception as e:
            logging.exception("Error while adjusting throttle to {!s} "
                              "on pin {!s}".format(throttle, self.pin))
            return False


class Quadcopter():
    """ Class to control the quadcopter """

    def __init__(self):
        pigpiod_running = self._is_daemon_running()
        if not pigpiod_running:
            logging.error("pigpio daemon was not started successfully")
            raise Exception("pigpiod daemon did not start properly. "
                            "Check permissions and / or if installed properly")
        self.pi = pigpio.pi()
        # TODO: call self.pi.stop() in the end...
        if not self.pi.connected:
            # no connection to the GPIO pins possible...
            logging.error("Unable to connect to the GPIO pins (pigpio: {!s}). "
                          "Is the pigpiod daemon running?"
                          .format(self.pi.__dict__))
            raise Exception("Unable to connecto to the GPIO pins")

        self._gyro_sensor = self._init_gyrosensor()
        # TODO add check if gyro is started properly...
        self.min_throttle = config.get_min_throttle()
        self.max_throttle = config.get_max_throttle()
        self.start_signal = 1000
        self.stop_signal = 0
        self._motor_front_left = self._init_motor(config.
                                                  get_motor_front_left_pin())
        self._motor_front_right = self._init_motor(config.
                                                   get_motor_front_right_pin())
        self._motor_back_left = self._init_motor(config.
                                                 get_motor_back_left_pin())
        self._motor_back_right = self._init_motor(config.
                                                  get_motor_back_right_pin())

    def _init_gyrosensor(self):
        """ Returns an initialized Gyrosensor object """
        # TODO: add scaling factors to the sensor ...
        address = config.get_gyrosensor_address()
        return mpu6050.mpu6050(address)

    def _init_motor(self, pin):
        """ Returns an initialized Motor object """
        return Motor(self.pi, pin, self.start_signal, self.stop_signal,
                     self.min_throttle, self.max_throttle)

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
            sample_rate = config.get_pigpiod_sample_rate()
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

    def turn_off(self):
        """ Sends stop signal to each motor and stops the pigpio.pi object """
        # TODO: add logic to bring the quadcopter safely home / down?
        success = True
        try:
            for motor in [self._motor_back_left, self._motor_back_right,
                          self._motor_front_left, self._motor_front_right]:
                success = motor.send_stop_signal()
                if not success:
                    logging.exception("Unable to stop motor: {!s}"
                                      .format(motor.__dict__))
                    success = False
            # self.pi.stop()
        except Exception as e:
            logging.critical("Exception occurred while sending the start "
                             "signal to the motors: {!s}".format(e))
            success = False

        return success

    def turn_on(self):
        """ Sends start signal to each motor """
        try:
            for motor in [self._motor_back_left, self._motor_back_right,
                          self._motor_front_left, self._motor_front_right]:
                success = motor.send_start_signal()
                if not success:
                    logging.exception("Unable to start motor: {!s}"
                                      .format(motor.__dict__))
                    return False
            return True
        except Exception as e:
            logging.critical("Exception occurred while sending the start "
                             "signal to the motors: {!s}".format(e))
            return False

    def get_gyrosensor_temp(self):
        """ Returns the temperature of the gyrosensor in °C
        (rounded to one decimal) """
        rounded_temp = round(self._gyro_sensor.get_temp(), 1)
        logging.debug("Current gyrosensor temperature: {!s}°C"
                      .format(rounded_temp))
        return rounded_temp

    def _perform_gyrosensor_check(self):
        """ Checks if the gyrosensor is active and responding with
        appropriate data """
        logging.debug("Performing check if gyrosensor is responding and "
                      "returns valid values")
        temp = round(self.quadcopter.get_gyro_temp(), 0)
        in_range = temp in range(10, 40)
        logging.debug("Gyrosensor temperature measured: {!s}°C".format(temp))
        if in_range:
            logging.info("Gyrosensor temperature check PASSED")
        else:
            logging.info("Gyrosensor temperature check FAILED. "
                         "Could be too cold or too hot...")
            return False


# class Gyroscope():
#     """ Class to interface the gyrosensor """
#
#     def __init__(self, pi, pin):
#         address = config.get_gyrosensor_address()
#         self.sensor = mpu6050.mpu6050(address)
