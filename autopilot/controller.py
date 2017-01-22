import time
import pigpio

PIN = int(sys.argv[1])
if not PIN:
        print("ENTER PIN!")
        exit(1)
pi = pigpio.pi()
value = 1
while value > 0:
        value = int(input("INPUT: "))
        print("APPLYING %s" % value)
        pi.set_servo_pulsewidth(PIN, value)
