#include <string>
#include <iostream>
#include "wiringPi/wiringPi/wiringPi.h"
#include "motor.h"
#include "config.h"

#define FL_MOTOR 4 
#define MAX_PWM 1860

int main()
{
	std::cout << "Quadcopter Powering up" << std::endl;
	
	pi_drone::config::initialize();
	std::cout << "Setup GPIO" << std::endl;
	wiringPiSetupGpio();

	pi_drone::init_motors(100, { FL_MOTOR });

	while (true)
	{
		std::cout << "input a value between 180 and 1000" << std::endl;
		int new_pwm = 0;
		std::string input;
		std::cin >> input;
		new_pwm = std::stoi(input);
		std::cout << "updating pwm to " << new_pwm << std::endl;

		softServoWrite(FL_MOTOR, new_pwm);
	}
	return 0;
}
