#ifndef __MOTOR_PI_DRONE_H
#define __MOTOR_PI_DRONE_H

#include <string>
#include <vector>
#include "wiringPi/wiringPi/softServo.h"

#define FL_MOTOR 4
#define MAX_PWM 1860
namespace pi_drone
{

const int8_t NO_PIN = -1;

bool init_motors(uint16_t start_seq, std::vector<int8_t> pins)
{
	int8_t tmp_pins[8];
	for (size_t i = 0; i < sizeof(tmp_pins); ++i)
	{
		if (pins.size() > i)
		{
			tmp_pins[i] = pins[i];
		}
		else
		{
			tmp_pins[i] = NO_PIN;
		}
	}

	if (softServoSetup(tmp_pins[0], tmp_pins[1], tmp_pins[2], tmp_pins[3],
					tmp_pins[4], tmp_pins[5], tmp_pins[6], tmp_pins[7]))
	{
		return false;
	}

	for (const auto pin : pins)
	{
		softServoWrite(pin, start_seq);
	}

	return true;
}

class Motor
{
private:
	uint8_t pin;
	uint16_t start_seq;
	uint16_t min_throttle;
	uint16_t max_throttle;
	uint16_t curr_throttle;

	bool check_throttle_value(uint16_t value)
	{
		return value <= this->max_throttle && value >= this->min_throttle;
	}

public:
	Motor(uint8_t pin, uint16_t start_seq, uint16_t min_throttle, 
			uint16_t max_throttle)
		: pin(pin), start_seq(start_seq), min_throttle(min_throttle),
			max_throttle(max_throttle)
	{
		
	}

	bool send_throttle(uint16_t value)
	{
		if (!check_throttle_value(value))
		{
			return false;
		}
		softServoWrite(this->pin, value);
		return true;
	}

	uint16_t get_curr_throttle()
	{
		return this->curr_throttle;
	}
};

} // namespace pi_drone

#endif

//vim: tabstop=4 shiftwidth=4 noexpandtab
