from time import time, sleep, strftime, localtime
import RPi.GPIO as GPIO
from tkinter import *
from tkinter import ttk
from threading import Thread
import os
import argparse
import json

class Tick:
    GVF = 32.55
    CHARGE_mC = 0

    RECHARGING = 1
    DISCHARGING = -1

    def __init__(self, instant, direction):
        self.direction = direction
        self.instant = instant


class Counter:
    def __init__(self, create_csv, resistor_value):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()
        self.create_csv = create_csv
        self.file_name = ""
        self.create_history_file()

        Tick.CHARGE_mC = 1/(Tick.GVF * resistor_value) * 1000
        print("---> CHARGE_mC: {}".format(Tick.CHARGE_mC))

    def create_history_file(self):
        if self.create_csv:
            if not os.path.exists('history'):
                os.makedirs('history')

            self.file_name = "history/history_{}.csv".format(
                                   strftime('%Y-%m-%d %H:%M:%S', localtime(time())).replace(' ', '_'))
            with open(self.file_name, 'w') as file:
                file.write('time_absolute,time_relative,direction\n')
        else:
            self.file_name = "csv file creation deactivated"

    def add_tick(self, instant, direction):
        tick = Tick(instant, direction)
        self.ticks.append(tick)
        self.accumulated_charge += tick.CHARGE_mC * tick.direction
        self.avg_current = self.accumulated_charge/(time()-self.start)

        if self.create_csv:
            with open(self.file_name, 'a') as file:
                file.write('{},{},{}\n'.format(time(), time()-self.start, direction))

    def reset(self):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()
        self.create_history_file()


class Gui:
    def __init__(self):
        root = Tk()
        self.root = root

        self.time_elapsed = StringVar()
        self.number_of_ticks = StringVar()
        self.total_charge = StringVar()
        self.avg_current = StringVar()
        self.file_name = StringVar()
        self.resistor_value = StringVar()
        self.charge_mc = StringVar()

        self.root.title("AMP-O-METER")

        self.mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        ttk.Label(self.mainframe, textvariable=self.time_elapsed).grid(column=1, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.number_of_ticks).grid(column=2, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.total_charge).grid(column=3, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.avg_current).grid(column=4, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.file_name).grid(columnspan=2, column=2, row=3, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.resistor_value).grid(column=2, row=4, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.charge_mc).grid(column=4, row=4, sticky=(W, E))

        ttk.Label(self.mainframe, text="Time elapsed:").grid(column=1, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total ticks:").grid(column=2, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total charge (mC):").grid(column=3, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Avg current (mA):").grid(column=4, row=1, sticky=W)
        ttk.Label(self.mainframe, text="History file:").grid(column=1, row=3, sticky=W)
        ttk.Label(self.mainframe, text="Resistor value:").grid(column=1, row=4, sticky=W)
        ttk.Label(self.mainframe, text="mC per tick:").grid(column=3, row=4, sticky=W)

        # self.recharge_button = ttk.Button(self.mainframe, text="Recharge tick").grid(column=1, row=3, sticky=W)
        self.reset_button = ttk.Button(self.mainframe, text="Reset")
        self.reset_button.grid(column=4, row=3, sticky=W)

        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            GPIO.cleanup()


class Controller:
    def __init__(self, polarity_pin=16, interrupt_pin=20, create_csv=False, resistor_value=4.7):
        print("---> resistor: {}".format(resistor_value))
        print("---> csv: {}".format(create_csv))

        if create_csv == "on":
            create_csv = True
        else:
            create_csv = False

        print("---> csv: {}".format(create_csv))

        self.resistor_value = resistor_value
        self.polarity_pin = polarity_pin
        self.interrupt_pin = interrupt_pin
        self.vio_pin = 21

        self.counter = Counter(create_csv, resistor_value)
        self.gui = Gui()

        self.update_time_thread = Thread(target=self.update_time_elapsed, daemon=True)
        self.update_time_thread.start()

        # self.gui.recharge_button.bind("<Button>", self.add_tick)
        self.gui.reset_button.bind("<Button>", self.reset)

        self.gui.file_name.set("Waiting for first tick...")
        self.did_tick = False
        self.gui.resistor_value.set("{:.3g} ohms".format(resistor_value))
        self.gui.charge_mc.set("{:.4g} mC".format(Tick.CHARGE_mC))

    def reset(self, _):
        self.counter.reset()
        self.gui.file_name.set("Waiting for first tick...")
        self.gui.number_of_ticks.set("")
        self.gui.total_charge.set("")
        self.gui.avg_current.set("")

    def run(self):
        self.setup_probe()
        self.gui.run()

    def add_tick(self, direction=Tick.DISCHARGING):
        if not self.did_tick:
            self.counter.start = time()
            self.update_gui()
            self.did_tick = True
        else:
            instant = time()
            self.counter.add_tick(instant, direction)
            self.update_gui()

    def update_gui(self):
        self.gui.number_of_ticks.set(len(self.counter.ticks))
        self.gui.total_charge.set("{:8.5f}".format(self.counter.accumulated_charge))
        self.gui.avg_current.set("{:5.3f}".format(self.counter.avg_current))
        self.gui.file_name.set(self.counter.file_name)

    def update_time_elapsed(self):
        while True:
            hours, rem = divmod(time() - self.counter.start, 3600)
            minutes, seconds = divmod(rem, 60)
            self.gui.time_elapsed.set("{:0>2}:{:0>2}:{:02.0f}".format(int(hours), int(minutes), seconds))
            sleep(1)

    def setup_probe(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.polarity_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.setup(self.vio_pin, GPIO.OUT)
        GPIO.output(self.vio_pin, GPIO.HIGH)

        GPIO.add_event_detect(self.interrupt_pin, GPIO.FALLING, callback=self.probe_callback)

    def probe_callback(self, _):
        polarity = GPIO.input(self.polarity_pin)
        if polarity:
            polarity = Tick.RECHARGING
        else:
            polarity = Tick.DISCHARGING

        self.add_tick(polarity)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv")
    parser.add_argument("--resistor")
    try:
        args = parser.parse_args()
    except:
        print("Unknown arguments passed")
        raise Exception


    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except:
        config = {
            "resistor_value": 4.7,
            "enable_csv": "off"
        }


    if args.resistor is not None:
        config["resistor_value"] = float(args.resistor)

    if args.csv is not None:
        if args.csv == "on" or args.csv == "off":
            config["enable_csv"] = args.csv
        else:
            print("Unknown value of option '--csv'. Please choose either 'on' or 'off' (without quotes)")
            raise Exception

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)


    controller = Controller(create_csv=config["enable_csv"], resistor_value=config["resistor_value"])

    controller.run()
