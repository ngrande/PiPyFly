""" Configuration Module - autom. loads the config.ini file and checks it.
Also sets up the loggin module so all other modules do not have to worry
about that and can use it out of the box."""

import os
import configparser
import logging
import re

# TODO: add a validation for the configuration (if al values are set)
# config_validation = {'ESC': }


def verify_config_ini(config_ini):
    """ Verifies the config.ini file (using regular expressions) - to avoid
    wrong inputs """
    verify_dict = {
        "AERO": {"PropSize": "([1-9][0-9]+|[1-9])x[1-9]+(([.][1-9])*)"},
        # TODO: add logical check -> i.e. maximum should be higher than min
        "ESC": {"Maximum": "[1-9][0-9]*",
                "Minimum": "[1-9][0-9]*"},
        "PIN": {"MotorFrontLeft": "[1-9][0-9]{0,1}",
                "MotorFrontRight": "[1-9][0-9]{0,1}",
                "MotorBackLeft": "[1-9][0-9]{0,1}",
                "MotorBackRight": "[1-9][0-9]{0,1}"},
        # TODO add logical check to see if it is a valid posix filename
        "LOG": {"Level": "(?i)(critical|error|warning|info|debug|notset)",
                "OutputFile": "[a-zA-Z0-9]+.*"},
        "PIGPIOD": {"SampleRate": "(?i)(1|2|4|5|8|10)"},
        "GYRO": {"Address": "0x[0-9a-f]+",
                 # TODO add logical check to check that TiltFront and TiltLeft
                 # are not the same
                 "TiltFront": "[+-][xyz]",
                 "TiltLeft": "[+-][xyz]"}
    }

    for section, checks in verify_dict.items():
        for name, regex_check in checks.items():
            ini_value = config_ini[section][name]
            matches = re.fullmatch(regex_check, ini_value)
            if not matches:
                raise Exception("Configuration is corrupted => "
                                "section: {!s}, name: {!s}, value: {!s}"
                                .format(section, name, ini_value))
                return False
            else:
                continue
    return True

config = configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/config.ini')
if len(config.sections()) == 0:
    raise Exception("No configuration set in the file config.ini")
verify_config_ini(config)


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
    elif log_level-str == 'notset':
        return logging.NOTSET


def get_log_output_file():
    """ Returns the log output filename. """
    return str(config['LOG']['OutputFile'])


def get_pigpiod_sample_rate():
    """ Returns the pigpiod sample rate (int) which should be used when
    starting the daemon """
    return int(config['PIGPIOD']['SampleRate'])


def get_gyrosensor_address():
    """ Returns a int of the hexadecimal address value """
    return int(config['GYRO']['Address'], 16)


def get_gyrosensor_tilt_front_axis():
    """ Returns a string indicating which axis will be affected in which way
    when the drone tilts to the front (nose) """
    return str(config['GYRO']['TiltFront'])


def get_gyrosensor_tilt_left_axis():
    """ Returns a string indicating which axis will be affected in which way
    when the drone tilts to the left """
    return str(config['GYRO']['TiltLeft'])


# configure the logging module (so all other modules are already
# configured for logging)
log_level = get_log_level()
log_output_file = get_log_output_file()
logging.basicConfig(filename=log_output_file, level=log_level)
