#ifndef __MOTOR_PI_DRONE_H
#define __MOTOR_PI_DRONE_H

#include <string>
#include <unordered_map>
#include <cassert>
#include <vector>

#include "wiringPi/wiringPi/softServo.h"
#include "config.h"

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
	bool cw_rotation;
	uint16_t start_seq;
	uint8_t curr_throttle; ///< curr throttle on the map (0-100)
	bool started;
	std::unordered_map<uint8_t, uint16_t> throttle_map;

	void init_throttle_map(uint16_t min, uint16_t max)
	{
		uint16_t step = (max - min) / 99;
		uint16_t one_perc = min - step; // so at 1% we will have min throttle
		for (size_t i = 0; i < 101; ++i)
		{
			throttle_map.insert({i, one_perc + (step * i)});
		}

		assert(throttle_map.size() == 100);
	}

	bool translate_value_to_throttle(uint8_t value, uint16_t& throttle_out)
	{
		if (value > 100 /* || value < 0 - we dont need this check
		because it is an unsigned int */)
		{
			// __LOGGING__
			return false;
		}
		
		auto it = throttle_map.find(value);
		// it should always find a value inbetween 0 - 100
		// otherwise the code is broken
		assert(it != throttle_map.end());
		throttle_out = it->second;
		return true;
	}

public:
	Motor(uint8_t _pin, bool _cw_rotation, uint16_t _start_seq, 
			uint16_t _min_throttle, uint16_t _max_throttle)
		: pin(_pin), cw_rotation(_cw_rotation), start_seq(_start_seq),
		curr_throttle(0), started(false)
	{
		init_throttle_map(_min_throttle, _max_throttle);
	}

	bool start()
	{
		if (started)
		{
			return false;
		}

		softServoWrite(pin, config::s_start_signal);

		started = true;
		curr_throttle = 0;

		// __LOGGING__

		return true;
	}
	
	bool stop()
	{
		if (!started)
		{
			return false;
		}

		softServoWrite(pin, config::s_stop_signal);
		curr_throttle = 0;
		
		// __LOGGING__

		return true;
	}

	bool send_throttle(uint8_t value)
	{
		uint16_t throttle;
		if (!translate_value_to_throttle(value, throttle))
		{
			return false;
		}
		softServoWrite(this->pin, throttle);
		return true;
	}

	uint8_t get_curr_throttle()
	{
		return this->curr_throttle;
	}

	uint16_t get_curr_throttle_real()
	{
		auto it = throttle_map.find(curr_throttle);
		// we expect this to be in range
		// because the map is filled already
		// and the curr_throttle value is set by us correctly
		assert(it != throttle_map.end());
		return it->second;
	}
};

} // namespace pi_drone

#endif

//vim: tabstop=4 shiftwidth=4 noexpandtab
