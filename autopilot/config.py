import configparser

# TODO: add a validation for the configuration (if al values are set)
# config_validation = {'ESC': }


class ConfigInterpreter():
    """ Reads the configuration 'config.ini' and gives an easy to use
    interface for reading the values (with the correct type) """
    def __init__(self):
        self.config = self._read_configuration()

    def _read_configuration(self):
        config = configparser.ConfigParser()
        config.read('./config.ini')
        if len(config.sections()) == 0:
            raise Exception("No configuration set in the file config.ini")
        return config

    def get_prop_size(self):
        """ Returns size of the propellers as a string (11x5 or 9x4.7) """
        return str(self.config['AERO']['PropSize'])

    def get_max_throttle(self):
        """ Returns the maximum throttle of the ESC """
        return int(self.config['ESC']['MAXIMUM'])

    def get_min_throttle(self):
        """ Returns the minimum throttle of the ESC """
        return int(self.config['ESC']['MINIMUM'])

    def get_motor_front_left_pin(self):
        """ Returns the pin number (BMC) of the 1st motor (front left) """
        return int(self.config['PIN']['MotorFrontLeft'])

    def get_motor_front_right_pin(self):
        """ Returns the pin number (BMC) of the 2nd motor (front right) """
        return int(self.config['PIN']['MotorFrontRight'])

    def get_motor_back_left_pin(self):
        """ Returns the pin number (BMC) of the 4th motor (back left) """
        return int(self.config['PIN']['MotorBackLeft'])

    def get_motor_back_right_pin(self):
        """ Returns the pin number (BMC) of the 3rd motor (back right) """
        return int(self.config['PIN']['MotorBackRight'])
