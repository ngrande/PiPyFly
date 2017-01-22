import os
import configparser
import logging

# TODO: add a validation for the configuration (if al values are set)
# config_validation = {'ESC': }


# Unleash out of class? So that this config is always loaded and ready to use
# just as soon as the moudle is imported? Because it also sets up logging

# class ConfigInterpreter():
#     """ Reads the configuration 'config.ini' and gives an easy to use
#     interface for reading the values (with the correct type).
#     IMPORTANT: Also configures the logging module (So you do not have to
#     worry about this) """
#     def __init__(self):
#         self.config = self._read_configuration()
#         # configure the logging module (so all other modules are already
#         # configured for logging)
#         log_level = self.get_log_level()
#         log_output_file = self.get_log_output_file()
#         logging.basicConfig(filename=log_output_file, level=log_level)
#
#     def _read_configuration(self):
#         config = configparser.ConfigParser()
#         config.read('./config.ini')
#         if len(config.sections()) == 0:
#             raise Exception("No configuration set in the file config.ini")
#         return config
#
#     def get_prop_size(self):
#         """ Returns size of the propellers as a string (11x5 or 9x4.7) """
#         return str(self.config['AERO']['PropSize'])
#
#     def get_max_throttle(self):
#         """ Returns the Maximum throttle of the ESC """
#         return int(self.config['ESC']['Maximum'])
#
#     def get_min_throttle(self):
#         """ Returns the Minimum throttle of the ESC """
#         return int(self.config['ESC']['Minimum'])
#
#     def get_motor_front_left_pin(self):
#         """ Returns the pin number (BMC) of the 1st motor (front left) """
#         return int(self.config['PIN']['MotorFrontLeft'])
#
#     def get_motor_front_right_pin(self):
#         """ Returns the pin number (BMC) of the 2nd motor (front right) """
#         return int(self.config['PIN']['MotorFrontRight'])
#
#     def get_motor_back_left_pin(self):
#         """ Returns the pin number (BMC) of the 4th motor (back left) """
#         return int(self.config['PIN']['MotorBackLeft'])
#
#     def get_motor_back_right_pin(self):
#         """ Returns the pin number (BMC) of the 3rd motor (back right) """
#         return int(self.config['PIN']['MotorBackRight'])
#
#     def get_log_level(self):
#         """ Returns the confgiured logging.level """
#
#         log_level_str = str(self.config['LOG']['Level']).lower()
#         if log_level_str == 'debug':
#             return logging.DEBUG
#         elif log_level_str == 'info':
#             return logging.INFO
#         elif log_level_str == 'warning':
#             return logging.WARNING
#         elif log_level_str == 'error':
#             return logging.ERROR
#         elif log_level_str == 'critical':
#             return logging.CRITICAL
#
#     def get_log_output_file(self):
#         """ Returns the log output filename. """
#         return str(self.config['LOG']['OutputFile'])

# ---------------------------------------------------
# ---------------------------------------------------

# WORKAROUND: Make it moulde wide available


def get_prop_size():
    """ Returns size of the propellers as a string (11x5 or 9x4.7) """
    return str(config['AERO']['PropSize'])


def get_max_throttle():
    """ Returns the Maximum throttle of the ESC """
    return int(config['ESC']['Maximum'])


def get_min_throttle():
    """ Returns the Minimum throttle of the ESC """
    return int(config['ESC']['Minimum'])


def get_motor_front_left_pin():
    """ Returns the pin number (BMC) of the 1st motor (front left) """
    return int(config['PIN']['MotorFrontLeft'])


def get_motor_front_right_pin():
    """ Returns the pin number (BMC) of the 2nd motor (front right) """
    return int(config['PIN']['MotorFrontRight'])


def get_motor_back_left_pin():
    """ Returns the pin number (BMC) of the 4th motor (back left) """
    return int(config['PIN']['MotorBackLeft'])


def get_motor_back_right_pin():
    """ Returns the pin number (BMC) of the 3rd motor (back right) """
    return int(config['PIN']['MotorBackRight'])


def get_log_level():
    """ Returns the confgiured logging.level """

    log_level_str = str(config['LOG']['Level']).lower()
    if log_level_str == 'debug':
        return logging.DEBUG
    elif log_level_str == 'info':
        return logging.INFO
    elif log_level_str == 'warning':
        return logging.WARNING
    elif log_level_str == 'error':
        return logging.ERROR
    elif log_level_str == 'critical':
        return logging.CRITICAL


def get_log_output_file():
    """ Returns the log output filename. """
    return str(config['LOG']['OutputFile'])


config = configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/config.ini')
if len(config.sections()) == 0:
    raise Exception("No configuration set in the file config.ini")
# configure the logging module (so all other modules are already
# configured for logging)
log_level = get_log_level()
log_output_file = get_log_output_file()
logging.basicConfig(filename=log_output_file, level=log_level)
