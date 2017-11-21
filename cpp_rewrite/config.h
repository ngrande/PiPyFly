#ifndef __CONFIG_PI_DRONE_H
#define __CONFIG_PI_DRONE_H

#include <string>
#include <fstream>

namespace pi_drone
{
class config
{
	public:
		static bool initialize()
		{
			std::ifstream conf_file("config.ini");
			try
			{
				std::string line;
				while (std::getline(conf_file, line))
				{
					auto pos = line.find("=");
					std::string key = line.substr(0, pos - 1);
					std::string val = line.substr(pos + 1);
				}
			}
			catch (const std::exception& e)
			{
				// log exception
				return false;
			}
			conf_file.close();
			return true;
		}

	private:
		// disallow to create an instance of this class
		config() {}

		int8_t motor_fl_pin = -1;
		int8_t motor_fr_pin = -1;
		int8_t motor_rr_pin = -1;
		int8_t motor_rl_pin = -1;
		uint16_t start_seq = 0;
		uint16_t min_throttle = 0;
		uint16_t max_throttle = 0;

};
}

#endif
