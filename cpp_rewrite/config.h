#ifndef __CONFIG_PI_DRONE_H
#define __CONFIG_PI_DRONE_H

#include <string>
#include <iostream>
#include <fstream>
#include <unordered_map>

namespace pi_drone
{

// TODO: make this class somewhat nicer... it is horrible to manage new settings!
class config
{
	public:

		static int8_t s_motor_fl_pin;
		static int8_t s_motor_fr_pin;
		static int8_t s_motor_rr_pin;
		static int8_t s_motor_rl_pin;
		static bool s_motor_fl_cw;
		static bool s_motor_fr_cw;
		static bool s_motor_rl_cw;
		static bool s_motor_rr_cw;
		static uint16_t s_start_signal;
		static uint16_t s_stop_signal;
		static uint16_t s_min_throttle;
		static uint16_t s_max_throttle;

		static bool initialize()
		{
			//init_values();

			std::ifstream conf_file("config.ini");
			bool success = true;
			try
			{
				std::unordered_map<std::string, std::string> config_map;
				std::string line;
				while (std::getline(conf_file, line))
				{
					auto pos = line.find("=");
					if (pos == std::string::npos)
					{
						continue;
					}

					std::string key = line.substr(0, pos);
					std::string val = line.substr(pos + 1);
					config_map.insert({key, val});
				}

				s_motor_fl_pin = std::stoi(config_map.at("motor_fl_pin"));
				s_motor_fr_pin = std::stoi(config_map.at("motor_fr_pin"));
				s_motor_rr_pin = std::stoi(config_map.at("motor_rr_pin"));
				s_motor_fl_cw = config_map.at("motor_fl_cw") == "cw";
				s_motor_fr_cw = config_map.at("motor_fr_cw") == "cw";
				s_motor_rr_cw = config_map.at("motor_rr_cw") == "cw";
				s_motor_rl_cw = config_map.at("motor_rl_cw") == "cw";
				s_motor_rl_pin = std::stoi(config_map.at("motor_rl_pin"));
				s_start_signal = std::stoi(config_map.at("start_signal"));
				s_stop_signal = std::stoi(config_map.at("stop_signal"));
				s_min_throttle = std::stoi(config_map.at("min_throttle"));
				s_max_throttle = std::stoi(config_map.at("max_throttle"));
			}
			catch (const std::exception& e)
			{
				// _LOGGING_ exception
				std::cout << "ERROR" << std::endl;
				success = false;
			}
			conf_file.close();
			return success;
		}

	private:
		// disallow to create an instance of this class
		config() {}
};

int8_t config::s_motor_fl_pin = -1;
int8_t config::s_motor_fr_pin = -1;
int8_t config::s_motor_rr_pin = -1;
int8_t config::s_motor_rl_pin = -1;
bool config::s_motor_fl_cw = false;
bool config::s_motor_fr_cw = false;
bool config::s_motor_rl_cw = false;
bool config::s_motor_rr_cw = false;
uint16_t config::s_start_signal = 100;
uint16_t config::s_stop_signal = 0;
uint16_t config::s_min_throttle = 0;
uint16_t config::s_max_throttle = 0;



}

#endif
