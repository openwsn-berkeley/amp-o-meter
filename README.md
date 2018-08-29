## AMP-O-METER

A script to measure the power consumed by any circuit with the use of a LTC4150 Coulomb Meter attached to a Raspberry Pi. It works by counting the number of times the interrupt pin goes down on the LTC4150 module and multiplying it by the equivalent charge (in the default case 614.439 mC). Due to the coulomb counter design it measures the power consumption of the load and of itself (which ranges from 100 to 350 uA).

The steps needed to reproduce the counter are below.


### 1. Hardware needed

Here is the list of the hardware used for the original meter. Some components can be changed for similar ones such as the screen without affecting how the script works, others however (notably the coulomb counter) can't be changed.

- Raspberry Pi 3 (with 16GB microSD card and micro usb power supply) (USD 55.00 [here][7])
- Kuman 3.5 inch display (with resolution of 480x320, capacitive touch and **XPT2046 touch controller**) (USD 28.00 [here][3])
- LTC4150 Coulomb Counter (with breakout board from SparkFun) (USD 12.95 [here][5])
- 2 jumper cables, 2 hooks (USd 8.95 [here][6]) and 4-pin female header


[3]: http://www.kumantech.com/kuman-35quot-320480-tft-lcd-display-with-case-for-raspberry-pi-pi-2-pi-3-model-b-sc11_p0247.html
[5]: https://www.sparkfun.com/products/12052
[6]: https://www.sparkfun.com/products/501
[7]: https://www.amazon.com/Raspberry-Pi-Official-Desktop-Starter/dp/B01CI58722/ref=sr_1_1?s=pc&ie=UTF8&qid=1504872134&sr=1-1-spons&keywords=raspberry+pi&psc=1


### 2. Preparing LTC4150

In order to hook it up with the Raspberry Pi (RPi) you first need to solder a few things:

1. First and foremost: solder the two jumpers (`SJ2` and `SJ3`) on its back so that it switches from 5V to 3.3V;
2. 4-pin female header: solder the header to the pins `VIO`, `INT`, `POL` and `GND` so that the female part is in the same side as the circuit (and opposite to those jumpers). Pins `CLR` and `SHDN` will remain disconnected;
3. Power cables: solder the two hooks to the power input of the counter and two jumper cables to the power output. Hooks with small cable length are preferable as they need to fit inside the case.

#### 2.5 Choosing the resistor and then changing

This sensor measures the current passed by measuring the voltage drop across a resistor called Rsense. Usually on SparkFun boards this has the value of 0.05 ohm, which results in a maximum current of 1 A and a minimum measurable current of 3 mA. However as our usual consumption isn't greater than 10 mA and maximum precision is needed, a different resistor must be chosen. As a rule of thumb greater resistors result in greater precision and lower maximum current.

The lower value of the resistor is calculated by dividing 0.05 V (the maximum voltage drop the counter can sense) by the maximum current to be consumed. The upper value of the resistor is calculated by dividing 0.00015 V (150 µV, the minimum voltage drop the counter can sense) by the precision wanted (for example 30 µA -> 0.00003 A). The above example results in a 5 ohm resistor. As this is not a usually found value, a 4.7 ohm resistor can be used as replacement without many problems.  

Once the resistor is calculated, replacing it is quite simple:

1. Desorder (or break) the surface mount resistor in the middle of the board between the two bigger holes;
2. Solder the new resistor either using the surface mount pads or those two holes;
3. Change the value via the command line interface (detailed below).

### 3. Assembly with RPi

First connect the counter to the last pins of the second row as depicted below. Then connect the two hooks to the power supply, the positive to `3.3V` (first pin) and the negative to `GND` (13nth pin in the first row), also in the image below. Finally attach the screen. Its pins must cover the beginning of the two GPIO pins rows covering the two hooks.

There are two ways of numbering the GPIO pins. One is referring to the the physical position of the pin in the board and the other is by the "Broadcom SOC channel" (BCM) number. In the code the later definition is used. A table with the corresponding connections can be fount below:

|                         | Board (Pi 3) |  BCM |
|-------------------------|:------------:|:----:|
| VIO (voltage reference) |      `pin 34`      |  `pin 21`  |
| INT (interrupt)         |      `pin 36`      |  `pin 20`  |
| POL (polarity)          |      `pin 38`      |  `pin 16`  |
| GND (polarity)          |      `pin 40`      |  `pin GND` |
| Power IN +              |      `pin  1`      | `pin 3.3V` |
| Power IN -              |      `pin 25`      |  `pin GND` |

The power source can be either the RPi's 3.3V pin or an external source from 3.3V to 9V. No more than 1A should pass the circuit.

![Alt text](/../images/img/img1.JPG?raw=true "Optional Title")
![Alt text](/../images/img/img2.JPG?raw=true "Optional Title")
![Alt text](/../images/img/img3.JPG?raw=true "Optional Title")


### 4. Raspbian setup + screen drivers

The first step is to flash the Raspbian image to the microSD card. As there are plenty of tutorials available on the Internet this step won't be covered here.

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

As explained above, you may need to change the resistor value, so in order for the counter to work properly, start the program the first time via the command line interface with the argument `--resistor` followed by its value (e.g. `python3 amp-o-meter.py --resistor 4.7`). This step is required only once. The default value of the resistor is 4.7 ohms.

For debugging and further analysis purposes a _csv_ file can be created with an absolute timestamp, a timestamp relative to the beginning and the direction of change (1 for charging and -1 for discharging) for each detected tick. This option is disabled by default and can be toggled on/off with the flag `--csv` followed by either `on` or `off` (e.g. `python3 amp-o-meter.py --csv on`).  

Finally, if you want to run the counter via the terminal without a GUI, you just need to append the flag `--terminal` to the command. This can be useful when accessing the RPi via _ssh_.

That's it! Your final setup should look like this:
![Alt text](/../images/img/img4.JPG?raw=true "Optional Title")


## Dependencies

The only dependencies are `Python 3` and the `RPi.GPIO` package that usually comes bundled with Raspbian (as of 2017-08-16).

