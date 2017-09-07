## AMP-O-METER

A script to measure the power consumed by any circuit with the use of a LTC4150 Coulomb Meter attached to a Raspberry Pi. It works by counting the number of times the interrupt pin went down on the LTC4150 module and multiplying it by the equivalent charge (in the default case 614.439 mC). Due to the coulomb counter design it measures the power consumption of the load and of itsel (which ranges from 100 to 350 uA).


## How to run

Symply go the the main directory and type `python3 simple_gui.py`. A GUI will appear and a _csv_ log file will be created. This _csv_ file containt the an absolute timestamp, a timestamp relative to the beginning and the direction of change (1 for charging and -1 for discharging) for each detected tick.

## Dependencies

The only dependencies are `Python 3` and the `RPi.GPIO` package that usually comes bundled with Raspbian (as of 2017-08-16).

## Physical setup

The LTC4150 counter needs at least 4 pint in order to work properly and a power source. By default these 4 pins are (in the Raspberry Pi's BCM pin numbering scheme):

- VIO (voltage reference): pin 21
- INT (interrupt): pin 20
- POL (polarity): pin 16
- GND (ground): GND (pin number 34 on the board)

The power source can be either the RPi's 3.3V pin or an external source from 3.3V to 9V. No more than 1A sould pass the circuit.

If interfacing with a 3.3V circuit the two jumpers on the back (SJ2 and SJ3) must be closed.

## Raspberry Pi setup

This additional setup allows one to use the Kuman screen with a XPT2046 controller attached to the RPi. It was based on the instructions found on [Waveshare's website][1]

[1]: http://www.waveshare.com/wiki/3.5inch_RPi_LCD_(A)
[2]: http://www.waveshare.com/w/upload/0/00/LCD-show-170703.tar.gz

1. Do a fresh install of Raspbian (tested only with the 2017-08-16 version)
2. Connect to a screen and monitor and boot it
3. Through the command `sudo raspi-config` in the terminal expand file system (`advenced -> expand file system`) and enable autologin (`boot opions -> desktop autologin`)
4. Download the [LCD-show-170703.tar.gz drivers][2]. Note that network connection is required while installing and run the following commands. The last command will cause RPi to reboot and the HDMI output wont work anymore (unless you run `./LCD-hdmi`).
~~~
tar xvf LCD-show-*.tar.gz
cd LCD-show/
chmod +x LCD35-show
./LCD35-show
~~~

In some cased it is necessary to delete `dtoverlay=ads7846` from the file `/boot/config.txt` in order to make the screen work properly after `apt-upgrade`
