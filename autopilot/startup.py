import time
import pigpio

# TODO: add logging!!!


class Motor():
    """ Class to contorl a single motor """
    def __init__(self, pi, pin, start_signal, stop_signal,
                 min_throttle, max_throttle):
        if not pi:
            raise Exception("Pi = None. Unable to take control over the motor")
        self.pi = pi
        self.pin = int(pin)
        self.start_signal = int(start_signal)
        self.stop_signal = int(stop_signal)
        self.min_throttle = int(min_throttle)
        self.max_throttle = int(max_throttle)
        self.current_throttle = 0
        self._started = False

    def is_started(self):
        return self._started

    def send_start_signal(self):
        """ Sends the start signal (initiation sequence) to the motor (pin).
        Returns True if successful otherwise False
        (also if already started). """
        if self._started:
            return False

        self.pi.set_servo_pulsewidth(self.pin, self.start_signal)
        self._started = True
        return True

    def send_stop_signal(self):
        """ Sends the stop signal to the motor (pin). Returns True if successful
        and otherwise False. """
        try:
            self.pi.set_servo_pulsewidth(self.pin, self.stop_signal)
            return True
        except Exception as e:
            return False

    def send_throttle_adjustment(self, throttle_add):
        """ increases / decreases the current throttle by the
        throttle_add value """
        pass

    def send_throttle(self, throttle):
        """ sets the current throttle to the new value """
        if throttle < self.min_throttle:
            raise Exception("Can not set throttle lower than the minimum")
        elif throttle > self.max_throttle:
            raise Exception("Can not set throttle higher than maximum")

        try:
            # TODO: add some checks like:
            # * throttle too high cmpared to current throttle?
            # Could hurt motors?
            # * throttle too low compared to current throttle?
            # Could hurt drone?
            self.pi.set_servo_pulsewidth(self.pin, throttle)
            return True
        except Exception as e:
            return False


class Quadcopter():
    """ Class to control the quadcopter """
    def __init__(self):
        self.pi = pigpio.pi()
