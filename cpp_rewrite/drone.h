#ifndef __DRONE_PI_DRONE_H
#define __DRONE_PI_DRONE_H

#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <cassert>
#include <utility>

#include "config.h"
#include "motor.h"
#include "sensor.h"

namespace pi_drone
{

class quadcopter
{
private:
	motion_sensor sensor;
	bool turned_on;
	Motor motor_fl;
	uint8_t motor_fl_offset; ///< offset (+-%) to balance motor fl
	Motor motor_fr;
	uint8_t motor_fr_offset; ///< offset (+-%) to balance motor fr
	Motor motor_rl;
	uint8_t motor_rl_offset; ///< offset (+-%) to balance motor rl
	Motor motor_rr;
	uint8_t motor_rr_offset; ///< offset (+-%) to balance motor rr
	std::vector<std::pair<Motor&, uint8_t&>> motors; ///< references all motors -> used to operate on all motors at once

public:
	quadcopter()
		: turned_on(false),
		  motor_fl(config::s_motor_fl_pin, config::s_motor_fl_cw, 
				   config::s_start_signal, config::s_stop_signal,
				   config::s_min_throttle, config::s_max_throttle),
		  motor_fl_offset(0),
		  motor_fr(config::s_motor_fr_pin, config::s_motor_fr_cw, 
				   config::s_start_signal, config::s_stop_signal,
				   config::s_min_throttle, config::s_max_throttle),
		  motor_fr_offset(0),
		  motor_rl(config::s_motor_rl_pin, config::s_motor_fl_cw, 
				   config::s_start_signal, config::s_stop_signal,
				   config::s_min_throttle, config::s_max_throttle),
		  motor_rl_offset(0),
		  motor_rr(config::s_motor_rr_pin, config::s_motor_rr_cw, 
				   config::s_start_signal, config::s_stop_signal,
				   config::s_min_throttle, config::s_max_throttle),
		  motor_rr_offset(0),
		  motors({ {motor_fl, motor_fl_offset}, 
				   {motor_fr, motor_fr_offset},
				   {motor_rl, motor_rl_offset},
				   {motor_rr, motor_rr_offset} })
	{
		// get sure that we have a normal rotation setting
		// and will not start yawing...
		assert(motor_fl.is_cw() != motor_fr.is_cw());
		assert(motor_rl.is_cw() != motor_rr.is_cw());
		assert(motor_fl.is_cw() != motor_rl.is_cw());

		sensor.subscribe([](const float yaw, const float pitch, const float roll) {
				std::cout << "YAW: " << yaw << std::endl;
				std::cout << "ROLL: " << pitch << std::endl;
				std::cout << "PITCH: " << roll << std::endl;
				});
	}

	bool turn_on()
	{
		bool success = false;
		for (auto& pair : motors)
		{
			success = std::get<0>(pair).send_start();
			if (!success)
			{
				// __LOGGING__
			}
		}

		turned_on = true;
		return success;
	}

	bool turn_off()
	{
		bool success = false;
		for (auto& pair : motors)
		{
			success = std::get<0>(pair).send_stop();
			if (!success)
			{
				// __LOGGING__
			}
		}

		turned_on = true;
		return success;
	}

	bool set_overall_throttle(uint8_t value)
	{
		// TODO: this is shit - because we have to set each motor separately
		// otherwise it will go in hover and go up or down and not stay
		// in the current pitch / yaw
		
		// we should use offsets - because each motor is unequally strong
		bool success = false;
		for (auto& pair : motors)
		{
			auto offset = std::get<1>(pair);
			auto motor = std::get<0>(pair);
			
			// set the throttle to value + offset (%)
			// this is simply used to balance unequally strong motors
			// offset should be calculated with the sensor data
			success = motor.send_throttle(value + (value / 100 * offset));

			if (!success)
			{
				// __LOGGING__
			}
		}
		return success;
	}
};

} // namespace pi_drone

#endif
