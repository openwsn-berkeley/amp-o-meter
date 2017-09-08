## AMP-O-METER

A script to measure the power consumed by any circuit with the use of a LTC4150 Coulomb Meter attached to a Raspberry Pi. It works by counting the number of times the interrupt pin went down on the LTC4150 module and multiplying it by the equivalent charge (in the default case 614.439 mC). Due to the coulomb counter design it measures the power consumption of the load and of itself (which ranges from 100 to 350 uA).

The steps needed to reproduce the counter are below.


### 1. Hardware needed

Here is the list of the hardware used for the original meter. Some components can be changed for similar ones such as the screen without affecting how the script works, others however (notably the coulomb counter) can't be changed.

- Raspberry Pi 3 (with 16GB microSD card and micro usb power supply)
- Kuman 3.5 inch display (with resolution of 480x320, capacitive touch and **XPT2046 touch controller**)
- LTC4150 Coulomb Counter (with breakout board from SparkFun)
- 2 jumper cables, 2 hooks and 4-pin female header


### 2. Preparing LTC4150

In order to hook it up with the Raspberry Pi (RPi) you first need to solder a few things:

1. First and foremost: solder the two jumpers (SJ2 and SJ3) on its back so that it doesn't fry the RPi
2. 4-pin female header: solder the header to the pins VIO, INT, POL and GND so that the female part is in the same side as the circuit (and opposite to those jumpers). Pins CLR and SHDN will remain disconnected
3. Power cables: solder the two hooks to the power input of the counter and two jumper cables to the power output.Hooks with small cable length are preferable as they need to fit inside the case.


### 3. Assembly with RPi

First connect the counter to the last pins of the second row as depicted bellow. Then connect the two hooks tp the power supply, the positive to 3.3V (first pin) and the negative to the 13nth pin on the first row, also in the image bellow. Finally attach the screen. Its pins must cover the beginning of the two GPIO pins rows covering the two hooks.

Following the BCM numbering scheme those 4 pins are:
- VIO (voltage reference): pin 21
- INT (interrupt): pin 20
- POL (polarity): pin 16
- GND (ground): GND (pin number 34 on the board)

The power source can be either the RPi's 3.3V pin or an external source from 3.3V to 9V. No more than 1A should pass the circuit.

### 4. Raspbian setup + screen drivers

The first step is to flash the Raspbian image to the microSD card. As there are plenty of tutorials available on the internet this step won't be covered here.

Next comes the installation of the driver needed for our screen. As it changes from screen to screen, we'll only cover our specific case. These steps were based on the instructions found on [Waveshare's website][1].

[1]: http://www.waveshare.com/wiki/3.5inch_RPi_LCD_(A)
[2]: http://www.waveshare.com/w/upload/0/00/LCD-show-170703.tar.gz


1. Do a fresh install of Raspbian (tested only with the 2017-08-16 Stretch version)
2. Connect the RPi to a screen and pc monitor (using hdmi) and boot it
3. Using the command `sudo raspi-config` in the terminal expand file system (`advanced -> expand file system`) and enable autologin (`boot opions -> desktop autologin`)
4. Download the [LCD-show-170703.tar.gz drivers][2] and run the following commands. Note that network connection is required while installing. The last command will cause RPi to reboot and the HDMI output wont work anymore (unless you run `./LCD-hdmi` which will switch the output again).
~~~
tar xvf LCD-show-*.tar.gz
cd LCD-show/
chmod +x LCD35-show
./LCD35-show
~~~

In some cases it is necessary to delete `dtoverlay=ads7846` from the file `/boot/config.txt` in order to make the screen work properly after `apt-upgrade`.


### 5. Getting the code

Now comes the part where we get the real code. We'll first clone the repository, then move some files to the Desktop folder and finally change some permissions so that the code can be executed with a double click.

```
git clone https://github.com/openwsn-berkeley/amp-o-meter.git
cd amp-o-meter/
cp amp-o-meter.py run.sh ~/Desktop/
cd ~/Desktop/
chmod +x run.sh
```

### 6. Running the code

The final step is to run the code. There are two ways of doing this, either from the terminal with the command `python3 amp-o-meter.py` or by double clicking `run.sh` in the Desktop.

For debugging and further analysis purposes a _csv_ file can be created with an absolute timestamp, a timestamp relative to the beginning and the direction of change (1 for charging and -1 for discharging) for each detected tick. This option is disables by default and can be enabled with the flag `--csv`. 



## Dependencies

The only dependencies are `Python 3` and the `RPi.GPIO` package that usually comes bundled with Raspbian (as of 2017-08-16).

