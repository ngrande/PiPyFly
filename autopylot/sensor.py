""" Wrapper for all sensors (reading) """

import logging
import time

import mpu6050.mpu6050 as mpu6050


class Gyrosensor():
    """ Wrapper class for the mpu6050 gyrosensor.
    Makes it easier to switch the module which communicates with the
    mpu6050 sensor easier later. Or we could even switch to a whole
    new sensor """
    def __init__(self, address):
        self.sensor = mpu6050(address)
        # configure the gyro sensor
        # let it here be hardcoded because maybe we'll change the sensor
        # in the future and then we won't be able to use the same configs
        self.sensor.set_gyro_range(mpu6050.GYRO_RANGE_250DEG)
        self.sensor.set_accel_range(mpu6050.ACCEL_RANGE_2G)

    def get_sensor_temperature(self):
        """ Returns the temperature of the gyrosensor in °C
        (rounded to one decimal) """
        rounded_temp = round(self.sensor.get_temp(), 1)
        logging.debug("Current gyrosensor temperature: {!s}°C"
                      .format(rounded_temp))
        return rounded_temp

    def get_acceleration_data(self):
        """ Returns the acceleration data measured by the gyrosensor """
        accel_data = self.sensor.get_accel_data()
        return accel_data

    def get_gyroscope_data(self):
        """ Returns the gyroscope data from the gyrosensor """
        gyro_data = self.sensor.get_gyro_data()
        return gyro_data

    def _perform_selfcheck(self):
        """ Checks if the gyrosensor is active and responding with
        appropriate data.
        This check should only be made while not flying. """
        logging.debug("Performing check if gyrosensor is responding and "
                      "returns valid values")
        temp = round(self.get_sensor_temperature(), 0)

        logging.debug("Gyrosensor temperature measured: {!s}°C".format(temp))
        if temp in range(10, 40):
            logging.info("Gyrosensor temperature check PASSED")
        else:
            logging.critical("Gyrosensor temperature check FAILED. "
                             "Could be too cold or too hot...")
            return False

        # TODO: add sampling of some more data for the test...

        gyro = self._sample_avg_data_gyro()
        logging.debug("Gyrosensor gyroscope data: {!s}".format(gyro))
        # if all([round(val, 0) == 0 for _, val in gyro.items()]):
        print(gyro)
        if round(gyro['x'], 0) == 0 and round(gyro['y'], 0) == 0 and round(gyro['z'], 0) in [10, -10]:
            logging.info("Gyrosensor gyroscope data check PASSED")
        else:
            logging.critical("Gyrosensor gyroscope data check FAILED. "
                             "Do not shake the device while checking...")
            return False

        accel = self._sample_avg_data_accel()
        logging.debug("Gyrosensor acceleration data: {!s}".format(accel))
        # if all([round(val, 0) == 0 for _, val in accel.items()]):
        print(accel)
        if round(accel['x'], 0) == 0 and round(accel['y'], 0) == 0 and round(accel['z'], 0) in [10, -10]:
            logging.info("Gyrosensor acceleration data check PASSED")
        else:
            logging.critical("Gyrosensor acceleration data check FAILED. "
                             "Do not move the device while checking...")
            return False

        # if you reach this point you have passed the test...
        return True

    def _dead_simple_avg_sampling(self, function, count):
        """ Samples data from the given function (count times) and returns the
        avg value """
        sample_set = list()
        for _ in range(0, count):
            sample_set.append(function())
            time.sleep(0.01)

        avg_x = 0
        avg_y = 0
        avg_z = 0
        for data in sample_set:
            avg_x += round(data['x'], 2)
            avg_y += round(data['y'], 2)
            avg_z += round(data['z'], 2)

        avg_x = avg_x / len(sample_set)
        avg_y = avg_y / len(sample_set)
        avg_z = avg_z / len(sample_set)
        avg = {'x': avg_x, 'y': avg_y, 'z': avg_z}
        return avg

    def _sample_avg_data_gyro(self):
        """ Samples some gyroscope data and returns the avg values """
        return self._dead_simple_avg_sampling(self.get_gyroscope_data, 50)

    def _sample_avg_data_accel(self):
        """ Samples some acceleration data and returns the avg values """
        return self._dead_simple_avg_sampling(self.get_acceleration_data, 50)
