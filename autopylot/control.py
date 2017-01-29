""" Module to provide easy access to the Quadcopter.
All pins here are referenced by the BCM (Broadcom SOC channel) mapping """

# standard modules
import os
import time
import logging
import subprocess
import enum

# pip installed modules
import psutil
# import mpu6050
import pigpio

# my modules
import autopylot.sensor
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
# Always expect components to fails
# Expect the unexpected
# Priority Nr. 1: Be responsive and stay alive
###############################################################################

###############################################################################
# LIST OF TODOs
###############################################################################
# TODO implement controls (like changing tilt, or yaw)
# TODO add a worst case scenario handling for example if the gyro sensor
# fails in mid fly... or one / several motors stop responding.
# TODO: Write a wrapper for the gyrosensor so it is easier to change it later
#  to another module or sensor...
#
###############################################################################


class Motor():
    """ Class to contorl a single motor.
    There should not be a need to use this class - as it is
    already used by the Quadcopter class which will handle this """

    def __init__(self, pi, pin, cw_rotation, start_signal, stop_signal,
                 min_throttle, max_throttle):
        if not pi:
            logging.error("Pi = None. Unable to control the motor")
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
                                "responsivness or adjust the watchdog."
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
        wd_timeout_ms = 10
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
        one_perc = min_throttle - step  # to let min throttl be 1%
        for perc in range(0, 100 + 1):
            perc_to_value_dict[perc] = int(one_perc + (step * perc))

        return perc_to_value_dict

    def _convert_percent_to_actual_value(self, percent_val):
        """ Converts the percentage (throttle) value to the actual value.
        1% => min throttle and 100% => max throttle """
        #######################################################################
        # 1% => Min throttle
        # 100% => Max Throttle
        # these values are precalculated (and stored in a dict)
        # for faster computation
        #######################################################################
        verified_value = percent_val
        if percent_val not in range(0, 101):
            logging.error("percent_val ({!s}) was not within the valid "
                          "range from 0 to 100.".format(percent_val))
            if percent_val < 0:
                verified_value = 0
            elif percent_val > 100:
                verified_value = 100
            logging.warning("changed the percent_val input from {!s} to a "
                            "valid {!s}".format(percent_val, verified_value))
        actual_value = self._perc_value_map[verified_value]
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
            self.current_throttle = 0
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
        throttle_add value (in percent %) """
        new_total_throttle = int(self.current_throttle + throttle_add)
        logging.info("Sending throttle adjustment of {!s}% to current "
                     "throttle {!s}%".format(throttle_add,
                                             self.current_throttle))
        # easier and cleaner when just using the general function
        res = self.send_throttle(new_total_throttle)
        return res

    @verify_motor_started
    @check_throttle_change
    def send_throttle(self, throttle):
        """ sets the current throttle (in percent %) to the new value """
        throttle = int(throttle)
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
        self.min_throttle = autopylot.config.get_min_throttle()
        self.max_throttle = autopylot.config.get_max_throttle()
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

    def _init_gyrosensor(self):
        """ Returns an initialized Gyrosensor object """
        address = autopylot.config.get_gyrosensor_address()
        return autopylot.sensor.Gyrosensor(autopylot
                                           .config.get_gyrosensor_address())

    def _init_motor(self, pin, cw_rotation):
        """ Returns an initialized Motor object """
        return Motor(self.pi, pin, cw_rotation, self.start_signal,
                     self.stop_signal, self.min_throttle, self.max_throttle)

    def _check_motor_rotations(self):
        """ Checks if the quadcopter will be able to stay still (rotaiton should
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
        # TODO: add logic to bring the quadcopter safely home / down?
        overall_success = True
        try:
            for motor in self._for_each_motor():
                success = motor.send_stop_signal()
                if not success:
                    logging.critical("Unable to stop motor: {!s}"
                                     .format(motor.__dict__))
                    overall_success = False
            # self.pi.stop()
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
        except Exception as e:
            logging.exception("Exception occurred while sending the start "
                              "signal to the motors: {!s}".format(e))
            overall_success = False
        return overall_success

    def change_overall_throttle(self, throttle):
        """ Sends a throttle (%) adjustement to all motors. Valid value is
        between -100% to +100% """
        overall_success = True
        try:
            for motor in self._for_each_motor():
                success = motor.send_throttle_adjustment(throttle)
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

    def hover(self):
        """ Reads the current throttle of each motor and sets them to an equal
        level so the quadcopter should hover """
        # TODO: include sensor data in the processing here... (outline it
        # into another function / task)

        # NOTE: this is first very primitive because we will only set the
        # throttle to a equal level so it should hover (but only in an
        # environment without wind and stuff like that...)
        overall_success = True
        try:
            total_throttle = 0
            for motor in self._for_each_motor():
                total_throttle += motor.current_throttle

            throttle_foreach = int(total_throttle / 4)
            for motor in self._for_each_motor():
                success = motor.send_throttle(throttle_foreach)
                if not success:
                    logging.critical("Unable to send (absolute %) throttle "
                                     "({!s}) to motor: {!s}"
                                     .format(throttle_foreach, motor.__dict__))
                    overall_success = False
        except Exception as e:
            logging.exception("Exception occured while trying to bring the "
                              "motors on one level to hover: {!s}".format(e))
            overall_success = False

        return overall_success

    def change_yaw(self, absolute_yaw):
        """ Sends throttle (%) adjustements to the motors that result in a yaw.
        If the value is positive it will yaw clockwise and otherwise
        counterclockwise. Valid value is between -100 to +100%. This will
        change the throttle of each motor proportional to the absolute_yaw """
        # TODO
        # Edge cases:
        # Motor could already be at 100% throttle
        # NOTE: For the moment we can ignore the edge case when one or more
        # motors are already at 100% throttle... the yaw will still work but
        # not as fast or with a bit of altitude lose
        # Change each motor independently (because it could be tilted)
        if absolute_yaw < -100 or absolute_yaw > 100:
            logging.error("absolute_yaw exceeds +/- 100% ({!s})"
                          .format(absolute_yaw))
            return False

        overall_success = True
        try:
            for motor in self._for_each_motor():
                change_for_yaw = motor.current_throttle / 100 * absolute_yaw
                if absolute_yaw > 0 and not motor.cw_rotation:  # clockwise yaw
                    # clockwise yaw
                    change_for_yaw *= -1
                elif absolute_yaw < 0 and motor.cw_rotation:  # ccw yaw
                    # counterclockwise yaw
                    change_for_yaw *= -1
                else:  # if 0
                    pass  # placeholder for later

                success = motor.send_throttle_adjustment(change_for_yaw)
                if not success:
                    overall_success = False
                    logging.critical("Unable to send throttle adjustment for "
                                     "yaw ({!s}) to motor: {!s}"
                                     .format(absolute_yaw, motor.__dict__))
        except Exception as e:
            overall_success = False
            logging.exception("Exception occured while sending throttle "
                              "adjustment to motors to perform yaw: {!s}"
                              .format(e))
            return False
        return overall_success

    def change_tilt(self, side, adjustment):
        """ Change the tilt to the given side (front, left, frontleft,
        frontright) - to use the opssite side just use a negative value.
        Valid values for adjustment: -100% to +100%.
        I.e. you want to change tilt to rear you have to send: side=front
        and a negative adjustment value """
        overall_success = True
        try:
            ###################################################################
            # create a throttle list for the specific case
            # throttle list:
            # [0] = front_left
            # [1] = front_right
            # [2] = rear_right
            # [3] = rear_left
            ###################################################################
            throttle_list = []
            alternate_adj = adjustment * (-1)
            if side == self.TiltSide.front:
                # same adjustments for motor front_left and front_right
                # same adjustments for motor rear_left and rear_right
                throttle_list = [alternate_adj, alternate_adj, adjustment,
                                 adjustment]
            elif side == self.TiltSide.left:
                # same adjustments for motor front_left and rear_left
                throttle_list = [alternate_adj, adjustment, adjustment,
                                 alternate_adj]
            elif side == self.TiltSide.front_left:
                # only front_left and rear_right
                throttle_list = [alternate_adj, 0, adjustment, 0]
            elif side == self.TiltSide.front_right:
                throttle_list = [0, alternate_adj, 0, adjustment]
            else:
                logging.error("Invalid side value ({!s}). Can not compute the "
                              "motor throttle adjustments with this."
                              .format(side))
                overall_success = False
            success = self._change_throttle_by_list(throttle_list)
            if not success:
                logging.critical("Changing tilt was not successful. "
                                 "Something went wrong when changing "
                                 "tilt by throttle list.")
                overall_success = False
        except Exception as e:
            logging.exception("Exception occured while changing tilt: {!s}"
                              .format(e))
            overall_success = False
        return overall_success

    def _change_throttle_by_list(self, throttle_list):
        """ Change the throttle proportional (i.e. 50% of 50% current throttle
        -> 75% new current throttle) of each motor to
        by throttle_list (format => [front_left, front_right,
        rear_right, rear_left]). Valid values: -100% to +100% """
        overall_success = True

        if not throttle_list or len(throttle_list) == 0:
            logging.warning("throttle list did not include any values."
                            "Thus there did not happen any adjustments")
            return False

        def get_motor_by_index(index):
            if index == 0:
                return self._motor_front_left
            elif index == 1:
                return self._motor_front_right
            elif index == 2:
                return self._motor_rear_right
            elif index == 3:
                return self._motor_rear_left
            else:
                raise Exception("Index for motor out of range "
                                "({!s})".format(index))
        try:
            for index, throttle in enumerate(throttle_list):
                motor = get_motor_by_index(index)
                if throttle < -100 or throttle > 100:
                    overall_success = False
                    logging.error("throttle (%) adjustment ({!s}) for "
                                  "motor ({!s}) not within range (+-100%)"
                                  .format(throttle, motor.__dict__))
                throttle_adj = motor.current_throttle / 100 * throttle
                success = motor.send_throttle_adjustment(throttle_adj)
                if not success:
                    overall_success = False
                    logging.critical("Unable to send throttle (%) "
                                     "adjustment ({!s}) for motor: {!s}"
                                     .format(throttle, motor.__dict__))
        except Exception as e:
            logging.exception("Exception occured while changing tilt (by "
                              "throttle list): {!s}".format(e))
        return overall_success
