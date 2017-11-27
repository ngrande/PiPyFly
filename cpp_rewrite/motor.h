#ifndef __MOTOR_PI_DRONE_H
#define __MOTOR_PI_DRONE_H

#include <string>
#include <unordered_map>
#include <cassert>
#include <vector>
#include <iostream>

#include "wiringPi/wiringPi/softServo.h"

namespace pi_drone
{

const int8_t NO_PIN = -1;

bool init_motors(std::vector<int8_t> pins)
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
		// signalize the ESCs to get ready for takeoff!
		softServoWrite(pin, 0);
		// do not know why but i have to do it twice...
		softServoWrite(pin, 0);
	}

	return true;
}

class Motor
{
private:
	uint8_t pin;
	bool cw_rotation; ///< clockwise rotation - otherwise CCW
	uint16_t start_signal;
	uint16_t stop_signal;
	uint8_t curr_throttle; ///< curr throttle on the map (0-100)
	bool started;
	std::unordered_map<uint8_t, uint16_t> throttle_map;

	void init_throttle_map(uint16_t min, uint16_t max)
	{
		float step = (max - min) / 99.0;
		assert(step > 0);
		throttle_map.insert({0, 0});
		for (size_t i = 0; i < 100; ++i)
		{
			auto val = min + uint16_t(step * i + 0.5);
			throttle_map.insert({i + 1, val});
			std::cout << i + 1 << ": " << val << std::endl;
		}

		// start at 0 and end with 100
		assert(throttle_map.size() == 101);
	}

	bool translate_value_to_throttle(uint8_t value, uint16_t& throttle_out)
	{
		if (value > 100 /* || value < 0 - we dont need this check
		because it is an unsigned int */)
		{
			// __LOGGING__
			return false;
		}
		else if (value < 0) // clearly not possible with unsigned - but maybe we change it later
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
	Motor(uint8_t _pin, bool _cw_rotation, uint16_t _start_signal,
			uint16_t _stop_signal, uint16_t _min_throttle,
			uint16_t _max_throttle)
		: pin(_pin), cw_rotation(_cw_rotation), start_signal(_start_signal),
		stop_signal(_stop_signal), curr_throttle(0), started(false), 
		throttle_map({})
	{
		init_throttle_map(_min_throttle, _max_throttle);
	}

	bool send_start()
	{
		if (started)
		{
			return false;
		}

		//softServoWrite(pin, start_signal);

		started = true;
		curr_throttle = 0;

		// __LOGGING__

		return true;
	}
	
	bool send_stop()
	{
		if (!started)
		{
			return false;
		}

		softServoWrite(pin, stop_signal);
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
		curr_throttle = value;
		return true;
	}

	//void send_real(uint16_t val)
	//{
		//softServoWrite(this->pin, val);
	//}

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

	bool is_cw()
	{
		return cw_rotation;
	}
};

} // namespace pi_drone

#endif

//vim: tabstop=4 shiftwidth=4 noexpandtab
