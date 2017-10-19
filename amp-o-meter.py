import sys

if sys.version_info[0] < 3:
    print('You need to run this with Python 3')
    sys.exit(1)

from time      import time, sleep, strftime, localtime
from tkinter   import *
from tkinter   import ttk
from threading import Thread
import RPi.GPIO as GPIO
import traceback
import os
import argparse
import json
import statistics
import threading

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
        self.tick_diffs = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()
        self.create_csv = create_csv
        self.file_name = ""
        self.create_history_file()
        self.std_deviation_current = 0
        self.previous_tick_instant = None

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

        # TODO: test standard deviation calculation
        if self.previous_tick_instant is None:
            self.previous_tick_instant = instant
        else:
            self.tick_diffs.append(instant - self.previous_tick_instant)
            self.previous_tick_instant = instant
            mean = statistics.mean(self.tick_diffs)
            std_deviation_timediff = statistics.pstdev(self.tick_diffs)
            if std_deviation_timediff != 0:
                self.std_deviation_current = tick.CHARGE_mC/mean - tick.CHARGE_mC/(mean + std_deviation_timediff)
            # print("mean: {}, std_time: {}, std_cur: {}".format(mean, std_deviation_timediff, self.std_deviation_current))

        if self.create_csv:
            with open(self.file_name, 'a') as file:
                file.write('{},{},{}\n'.format(time(), time()-self.start, direction))

    def reset(self):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()
        self.create_history_file()


class TkGui:
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
        self.std_deviation_current = StringVar()

        self.root.title("AMP-O-METER")

        self.mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        ttk.Label(self.mainframe,          textvariable=self.time_elapsed).grid(column=1, row=2, sticky=(W, E))
        ttk.Label(self.mainframe,       textvariable=self.number_of_ticks).grid(column=2, row=2, sticky=(W, E))
        ttk.Label(self.mainframe,           textvariable=self.avg_current).grid(column=3, row=2, sticky=(W, E))
        ttk.Label(self.mainframe,          textvariable=self.total_charge).grid(column=4, row=2, sticky=(W, E))
        ttk.Label(self.mainframe,        textvariable=self.resistor_value).grid(column=1, row=4, sticky=(W, E))
        ttk.Label(self.mainframe,             textvariable=self.charge_mc).grid(column=2, row=4, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.std_deviation_current).grid(column=3, row=4, sticky=(W, E))
        ttk.Label(self.mainframe,             textvariable=self.file_name).grid(column=2, row=5, sticky=(W, E), columnspan=2)

        ttk.Label(self.mainframe,       text="Time elapsed:").grid(column=1, row=1, sticky=W)
        ttk.Label(self.mainframe,        text="Total ticks:").grid(column=2, row=1, sticky=W)
        ttk.Label(self.mainframe,   text="Avg current (mA):").grid(column=3, row=1, sticky=W)
        ttk.Label(self.mainframe,  text="Total charge (mC):").grid(column=4, row=1, sticky=W)
        ttk.Label(self.mainframe,     text="Resistor value:").grid(column=1, row=3, sticky=W)
        ttk.Label(self.mainframe,        text="mC per tick:").grid(column=2, row=3, sticky=W)
        ttk.Label(self.mainframe, text="Std deviation (mA):").grid(column=3, row=3, sticky=W)
        ttk.Label(self.mainframe,       text="History file:").grid(column=1, row=5, sticky=W)

        # self.recharge_button = ttk.Button(self.mainframe, text="Recharge tick").grid(column=1, row=3, sticky=W)
        self.reset_button = ttk.Button(self.mainframe, text="Reset")
        self.reset_button.grid(column=4, row=3, sticky=W, rowspan=3)

        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            GPIO.cleanup()


class TerminalUI:
    class Parameter:
        def __init__(self, description):
            self.value = ""
            self.description = description

        def __str__(self):
            return "{: <22}: {} \033[K".format(self.description, self.value)

        def set(self, new_value):
            self.value = str(new_value)

    def __init__(self):
        self.print_thread = threading.Thread(target=self.run, daemon=True)

        self.time_elapsed    = self.Parameter("Time elapsed")
        self.number_of_ticks = self.Parameter("Total ticks")
        self.total_charge    = self.Parameter("Total charge (mC)")
        self.avg_current     = self.Parameter("Avg current (mA)")
        self.file_name       = self.Parameter("History file")
        self.resistor_value  = self.Parameter("Resistor value")
        self.charge_mc       = self.Parameter("mC per tick")
        self.std_deviation_current = self.Parameter("Std deviation (mA)")


    def run(self):
        first_run = True

        while True:
            if not first_run:
                sys.stdout.write("\033[F"*10)

            print("\n ---- AMP-O-METER ---- \033[K")
            print(self.time_elapsed)
            print(self.number_of_ticks)
            print(self.avg_current)
            print(self.total_charge)
            print(self.resistor_value)
            print(self.charge_mc)
            print(self.std_deviation_current)
            print(self.file_name)

            first_run = False
            sleep(0.1)

class Controller:
    def __init__(self, polarity_pin, interrupt_pin, vio_pin, create_csv=False, resistor_value=4.7, terminal_ui=True):
        if create_csv == "on":
            create_csv = True
        else:
            create_csv = False

        self.resistor_value = resistor_value
        self.polarity_pin = polarity_pin
        self.interrupt_pin = interrupt_pin
        self.vio_pin = vio_pin
        self.terminal_gui = terminal_ui

        self.counter = Counter(create_csv, resistor_value)

        if self.terminal_gui:
            self.gui = TerminalUI()
        else:
            try:
                self.gui = TkGui()
                self.gui.reset_button.bind("<Button>", self.reset)
            except  TclError:
                # traceback.print_exc()
                print("\nAre you running this via shh? Either enable remote X server or run this script with the flag --terminal\n")

        self.gui.file_name.set("Waiting for first tick...")
        self.did_tick = False
        self.gui.resistor_value.set("{:.3g} ohms".format(resistor_value))
        self.gui.charge_mc.set("{:.4g} mC".format(Tick.CHARGE_mC))

        self.update_time_thread = Thread(target=self.update_time_elapsed, daemon=True)
        self.update_time_thread.start()

    def reset(self, _):
        self.counter.reset()
        self.gui.file_name.set("Waiting for first tick...")
        self.gui.number_of_ticks.set("")
        self.gui.total_charge.set("")
        self.gui.avg_current.set("")
        self.gui.std_deviation_current.set("")

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
        self.gui.total_charge.set("{:7.2f}".format(self.counter.accumulated_charge))
        self.gui.avg_current.set("{:5.3f}".format(self.counter.avg_current))
        self.gui.std_deviation_current.set("{:5.3f}".format(self.counter.std_deviation_current))
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

    # TODO: create a section on readme for these arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv")
    parser.add_argument("--resistor")
    parser.add_argument("--pol_pin")
    parser.add_argument("--int_pin")
    parser.add_argument("--vio_pin")
    parser.add_argument("--terminal", action='store_true')
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
            "enable_csv": "off",
            "pol_pin": 16,
            "int_pin": 20,
            "vio_pin": 21
        }


    if args.resistor is not None:
        config["resistor_value"] = float(args.resistor)

    if args.pol_pin is not None:
        config["pol_pin"] = int(args.pol_pin)

    if args.int_pin is not None:
        config["int_pin"] = int(args.int_pin)

    if args.vio_pin is not None:
        config["vio_pin"] = int(args.vio_pin)

    if args.csv is not None:
        if args.csv == "on" or args.csv == "off":
            config["enable_csv"] = args.csv
        else:
            print("Unknown value of option '--csv'. Please choose either 'on' or 'off' (without quotes)")
            raise Exception

    if args.terminal is not None:
        print(1)
        config["terminal_ui"] = False or args.terminal
    else:
        print(2)
        config["terminal_ui"] = True


    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)

    print("--- Run config: \n       resistor value: {}\n       csv: {}\n       create_gui: {}\n"
          "       pol_pin: {}\n       int_pin: {}\n       vio_pin: {}".format(config["resistor_value"],
                                                                                config["enable_csv"],
                                                                                config["terminal_ui"],
                                                                                config["pol_pin"],
                                                                                config["int_pin"],
                                                                                config["vio_pin"]))
    try:
        controller = Controller(create_csv=config["enable_csv"], resistor_value=config["resistor_value"], terminal_ui=config["terminal_ui"],
                                polarity_pin=config["pol_pin"], interrupt_pin=config["int_pin"], vio_pin=config["vio_pin"])
        controller.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print('\n\nScript ended normally!')
    except:
        traceback.print_exc()
        GPIO.cleanup()
        print('\r\n\nScript ended with an error')
