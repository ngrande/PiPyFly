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
		"AERO": {"propsize": "([1-9][0-9]+|[1-9])x[1-9]+(([.][1-9])*)"},
		# TODO: add logical check -> i.e. maximum should be higher than min
		"ESC": {"maximum": "[1-9][0-9]*",
				"minimum": "[1-9][0-9]*"},
		"MOTORS.PIN": {"motorfrontleft": "[1-9][0-9]{0,1}",
					"motorfrontright": "[1-9][0-9]{0,1}",
					"motorrearleft": "[1-9][0-9]{0,1}",
					"motorrearright": "[1-9][0-9]{0,1}"},
		"MOTORS.ROTATION": {"motorfrontleft": "(?i)(ccw|cw)",
							"motorfrontright": "(?i)(ccw|cw)",
							"motorrearleft": "(?i)(ccw|cw)",
							"motorrearright": "(?i)(ccw|cw)"},
		# TODO add logical check to see if it is a valid posix filename
		"LOG": {"level": "(?i)(critical|error|warning|info|debug|notset)",
				"outputfile": "[a-zA-Z0-9]+.*"},
		"PIGPIOD": {"samplerate": "(?i)(1|2|4|5|8|10)"},
		"GYRO": {"address": "0x[0-9a-f]+",
				# TODO add logical check to check that tiltfront and tiltleft
				# are not the same
				"tiltfront": "[+-][xyz]",
				"tiltleft": "[+-][xyz]"}
	}

	# instead of going through the checks we will iterate through the
	# config sections this has two benefits:
	# 1. we detect a missing check
	# 2. we are sure the whole config is checked
	for section in config_ini.sections():
		for key, value in config_ini[section].items():
			matches = re.fullmatch(verify_dict[section][key], value)
			if not matches:
				raise Exception("Configuration is corrupted => "
								"section: {!s}, key: {!s}, value: {!s}"
								.format(section, key, value))
				return False
	return True


config = configparser.ConfigParser()
# TODO: find a better place for the config.ini file
config.read(os.path.dirname(__file__) + '/config.ini')
if len(config.sections()) == 0:
	raise Exception("No configuration set in the file config.ini")
verify_config_ini(config)


def get_prop_size():
	""" Returns size of the propellers as a string (11x5 or 9x4.7) """
	return str(config['AERO']['propsize'])


def get_max_throttle():
	""" Returns the maximum throttle of the ESC """
	return int(config['ESC']['maximum'])


def get_min_throttle():
	""" Returns the minimum throttle of the ESC """
	return int(config['ESC']['minimum'])


def get_motor_front_left_pin():
	""" Returns the pin number (BMC) of the 1st motor (front left) """
	return int(config['MOTORS.PIN']['motorfrontleft'])


def get_motor_front_right_pin():
	""" Returns the pin number (BMC) of the 2nd motor (front right) """
	return int(config['MOTORS.PIN']['motorfrontright'])


def get_motor_rear_left_pin():
	""" Returns the pin number (BMC) of the 4th motor (rear left) """
	return int(config['MOTORS.PIN']['motorrearleft'])


def get_motor_rear_right_pin():
	""" Returns the pin number (BMC) of the 3rd motor (rear right) """
	return int(config['MOTORS.PIN']['motorrearright'])


def get_motor_front_left_rotation_is_cw():
	""" Returns True or False if the rotation of the 1st motor (front left) is
	clockwise """
	rotation_str = config['MOTORS.ROTATION']['motorfrontleft'].lower()
	return bool(True if rotation_str == 'cw' else False)


def get_motor_front_right_rotation_is_cw():
	""" Returns True or False if the rotation of the 2nd motor (front right) is
	clockwise """
	rotation_str = config['MOTORS.ROTATION']['motorfrontright'].lower()
	return bool(True if rotation_str == 'cw' else False)


def get_motor_rear_right_rotation_is_cw():
	""" Returns True or False if the rotation of the 3rd motor (rear right) is
	clockwise """
	rotation_str = config['MOTORS.ROTATION']['motorrearright'].lower()
	return bool(True if rotation_str == 'cw' else False)


def get_motor_rear_left_rotation_is_cw():
	""" Returns True or False if the rotation of the 4th motor (rear left) is
	clockwise """
	rotation_str = config['MOTORS.ROTATION']['motorrearleft'].lower()
	return bool(True if rotation_str == 'cw' else False)


def get_log_level():
	""" Returns the confgiured logging.level """

	log_level_str = str(config['LOG']['level']).lower()
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
	elif log_level_str == 'notset':
		return logging.NOTSET
	else:
		return logging.NOTSET


def get_log_output_file():
	""" Returns the log output filename. """
	return str(config['LOG']['outputfile'])


def get_pigpiod_sample_rate():
	""" Returns the pigpiod sample rate (int) which should be used when
	starting the daemon """
	return int(config['PIGPIOD']['samplerate'])


def get_gyrosensor_address():
	""" Returns a int of the hexadecimal address value """
	return int(config['GYRO']['address'], 16)


def get_gyrosensor_tilt_front_axis():
	""" Returns a string indicating which axis will be affected in which way
	when the drone tilts to the front (nose) """
	return str(config['GYRO']['tiltfront'])


def get_gyrosensor_tilt_left_axis():
	""" Returns a string indicating which axis will be affected in which way
	when the drone tilts to the left """
	return str(config['GYRO']['tiltleft'])


# configure the logging module (so all other modules are already
# configured for logging)
log_level = get_log_level()
log_output_file = get_log_output_file()
logging.basicConfig(filename=log_output_file, level=log_level,
					format="[%(asctime)s.%(msecs)03d] %(levelname)s "
					"[%(name)s.%(funcName)s:%(lineno)d] %(message)s",
					datefmt="%Y-%m-%d %H:%M:%S", )

# vim: tabstop=4 shiftwidth=4 noexpandtab
