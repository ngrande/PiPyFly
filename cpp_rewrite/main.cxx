#include <string>
#include <iostream>
#include "wiringPi/wiringPi/wiringPi.h"
#include "wiringPi/wiringPi/softServo.h"

#define FL_MOTOR 4
#define MAX_PWM 1860

int main()
{
	std::cout << "Quadcopter Powering up" << std::endl;

	// before we continue - lets check if we can use the software pwm
	// as in the python version.

	std::cout << "Setup GPIO" << std::endl;
	wiringPiSetupGpio();

	if (softServoSetup(FL_MOTOR, -1, -1, -1, -1, -1, -1, -1))
	{
		std::cout << "error initialising pwm pin" << std::endl;
	}
	softServoWrite(FL_MOTOR, 100);

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
