CC=gcc
CXX=g++

.PHONY: clean

make:
	$(CXX) wiringPi/wiringPi/softServo.c main.cxx -o FlyControl -lwiringPi -lpthread -std=c++1y -Wall -I/usr/local/include -L/usr/local/lib -LwiringPi/wiringPi

clean:
#	rm -f
