#!/usr/bin/env python2.7
# script by Alex Eames http://RasPi.tv
# http://RasPi.tv/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

pin = [13,19,26]

# GPIO 23 & 17 set up as inputs, pulled up to avoid false detection.
# Both ports are wired to connect to GND on button press.
# So we'll be setting up falling edge detection for both
GPIO.setup(pin[0], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin[1], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# GPIO 24 set up as an input, pulled down, connected to 3V3 on button press
GPIO.setup(pin[2], GPIO.IN, pull_up_down=GPIO.PUD_UP)


# now we'll define two threaded callback functions
# these will run in another thread when our events are detected
def my_callback(channel):
    print("falling edge detected on " + str(pin[0]))


def my_callback2(channel):
    print("falling edge detected on " + str(pin[1]))



# when a falling edge is detected on port 17, regardless of whatever
# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(pin[0], GPIO.FALLING, callback=my_callback, bouncetime=300)

# when a falling edge is detected on port 23, regardless of whatever
# else is happening in the program, the function my_callback2 will be run
# 'bouncetime=300' includes the bounce control written into interrupts2a.py
GPIO.add_event_detect(pin[1], GPIO.FALLING, callback=my_callback2, bouncetime=300)

try:
    print("Waiting for rising edge on port " + str(pin[2]))
    GPIO.wait_for_edge(pin[2], GPIO.RISING)
    print("Rising edge detected on port " + str(pin[0]) + ". Here endeth the third lesson.")

except KeyboardInterrupt:
    GPIO.cleanup()  # clean up GPIO on CTRL+C exit
GPIO.cleanup()  # clean up GPIO on normal exit
