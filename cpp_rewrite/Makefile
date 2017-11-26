CC=gcc
CXX=g++
CXXFLAGS= -Weffc++ -Wstrict-aliasing -Wwrite-strings -Winit-self -Wcast-align -Wpointer-airht -Wmissing-declarations -Wmissing-include-dirs -Wno-unused-parameter -Wuninitialized -Wshadow -Wall -Wextra

PROG=FlyControl

%.o: %.c
	$(CXX) $(CXXFLAGS) $< -o $@

all: $(PROG).o
	$(CXX) wiringPi/wiringPi/softServo.c \
		main.cxx \
		MotionSensor/libMotionSensor.a \
		libs/libI2Cdev.a \
		-o $(PROG) \
		-lwiringPi \
		-lpthread \
		-std=c++1y \
		-pedantic \
		-I/usr/local/include \
		-L/usr/local/lib \
		-LwiringPi/wiringPi

$(PROG).o: MotionSensor/libMotionSensor.a libs/libI2Cdev.a

MotionSensor/libMotionSensor.a:
	$(MAKE) -C MotionSensor/

libs/libI2Cdev.a:
	$(MAKE) -C libs/I2Cdev

clean:
	cd MotionSensor && $(MAKE) clean
	cd libs/I2Cdev && $(MAKE) clean
	rm -rf $(PROG)
