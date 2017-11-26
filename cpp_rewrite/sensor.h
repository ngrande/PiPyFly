#ifndef __SENSOR_PI_DRONE_H
#define __SENSOR_PI_DRONE_H

#include <functional>
#include <vector>
#include <thread>
//#define YAW 0
//#define PITCH 1
//#define ROLL 2
//#define DIM 3

extern float ypr[3]; //yaw, pitch, roll
extern float accel[3];
extern float gyro[3];
extern float temp;
extern float compass[3];

extern int ms_open();
extern int ms_update();
extern int ms_close();

namespace pi_drone
{
	const int YAW_IND = 0;
	const int PITCH_IND = 1;
	const int ROLL_IND = 2;


class motion_sensor
{
public:
	motion_sensor()
	{
	}

	~motion_sensor()
	{
		stop();
	}

	void start()
	{
		stopped = false;
		ms_open();
		std::thread t1(&motion_sensor::loop, this);
		t1.detach();
	}

	void stop()
	{
		stopped = true;
	}

	void subscribe(std::function<void(const float, const float, const float)> call_back)
	{
		ypr_callbacks.push_back(call_back);
	}
private:
	bool stopped = false;
	std::vector<std::function<void(const float, const float, const float)>> ypr_callbacks;

	void loop()
	{
		while (stopped == false)
		{
			ms_update();
			for (const auto& callback : ypr_callbacks)
			{
				float yaw = ypr[YAW_IND];
				float pitch = ypr[PITCH_IND];
				float roll = ypr[ROLL_IND];
				callback(yaw, pitch, roll);
			}
			// add delay here?
		}
	}
};
}

#endif
