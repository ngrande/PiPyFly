#ifndef __SENSOR_PI_DRONE_H
#define __SENSOR_PI_DRONE_H

#include <iostream>
#include <functional>
#include <vector>
#include <thread>
#include <cmath>
#include <assert.h>
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
		calibration_count = 0;
		calibrating = true;
		yaw_offset = 0;
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
	static const int CALIBRATION_TURNS = 100;
	bool stopped = false;
	bool calibrating = true;
	float pitch_rec[CALIBRATION_TURNS];
	float roll_rec[CALIBRATION_TURNS];
	float yaw_offset = 0;
	int calibration_count = 0;
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

				if (calibrating)
				{
					calibrate(yaw, pitch, roll);
				}
				else
				{
					callback(yaw - yaw_offset, pitch, roll);
				}
			}
			// add delay here?
		}
	}

	bool is_calmed_down(const float* arr, size_t size)
	{
		assert(size > 0);

		float sum = 0;
		for (size_t i = 0; i < size; ++i)
		{
			sum += arr[i];
		}

		if (sum == 0)
		{
			return true;
		}
		float avg = sum / size;
		return avg == arr[0];
	}

	void calibrate(const float yaw, const float pitch, const float roll)
	{
		float pitch_rounded = std::abs(std::round(pitch));
		float roll_rounded = std::abs(std::round(roll));

		if (calibration_count >= CALIBRATION_TURNS)
		{
			if (is_calmed_down(pitch_rec, CALIBRATION_TURNS) && is_calmed_down(roll_rec, CALIBRATION_TURNS))
			{
				yaw_offset = yaw;
				calibrating = false;
			}
			calibration_count = 0;
		}

		pitch_rec[calibration_count] = pitch_rounded;
		roll_rec[calibration_count] = roll_rounded;
		calibration_count++;
	}
};
}

#endif
