CC=gcc
CXX=g++

.PHONY: clean

make:
	$(CXX) wiringPi/wiringPi/softServo.c \
		main.cxx \
		-o FlyControl \
		-lwiringPi \
		-lpthread \
		-std=c++1y \
		-pedantic \
		-Weffc++ \
		-Wstrict-aliasing \
		-Wwrite-strings \
		-Winit-self \
		-Wcast-align \
		-Wpointer-arith \
		-Wmissing-declarations \
		-Wmissing-include-dirs \
		-Wno-unused-parameter \
		-Wuninitialized \
		-Wshadow \
		-Wall -Wextra \
		-I/usr/local/include \
		-L/usr/local/lib \
		-LwiringPi/wiringPi

clean:
#	rm -f
