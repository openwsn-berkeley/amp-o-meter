from time import time, sleep, strftime, localtime
import RPi.GPIO as GPIO
from tkinter import *
from tkinter import ttk
from threading import Thread
import os
import argparse


class Tick:
    CHARGE = 614.439
    RECHARGING = 1
    DISCHARGING = -1

    def __init__(self, instant, direction):
        self.direction = direction
        self.instant = instant


class Counter:
    def __init__(self, create_csv):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()
        self.create_csv = create_csv
        self.file_name = ""
        self.create_history_file()

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
        self.accumulated_charge += tick.CHARGE * tick.direction
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

        ttk.Label(self.mainframe, text="Time elapsed:").grid(column=1, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total ticks:").grid(column=2, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total charge (mC):").grid(column=3, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Avg current (mA):").grid(column=4, row=1, sticky=W)
        ttk.Label(self.mainframe, text="History file:").grid(column=1, row=3, sticky=W)

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
    def __init__(self, polarity_pin=16, interrupt_pin=20, create_csv=False):
        self.polarity_pin = polarity_pin
        self.interrupt_pin = interrupt_pin
        self.vio_pin = 21

        self.counter = Counter(create_csv)
        self.gui = Gui()

        self.update_time_thread = Thread(target=self.update_time_elapsed, daemon=True)
        self.update_time_thread.start()

        # self.gui.recharge_button.bind("<Button>", self.add_tick)
        self.gui.reset_button.bind("<Button>", self.reset)

        self.gui.file_name.set("Waiting for first tick...")
        self.did_tick = False

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
    parser.add_argument("--csv", action='store_true')
    try:
        args = parser.parse_args()
    except:
        print("Unknown arguments passed")
        raise

    if args.csv is not None:
        controller = Controller(create_csv=True)
    else:
        controller = Controller(create_csv=False)

    controller.run()
