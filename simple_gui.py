from time import time, sleep
import RPi.GPIO as GPIO
from tkinter import *
from tkinter import ttk
from threading import Thread

class Tick():
    CHARGE = 614.439
    RECHARGING = 1
    DISCHARGING = -1

    def __init__(self, instant, direction):
        self.direction = direction
        self.instant = instant

class Counter():
    def __init__(self):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()

    def add_tick(self, instant, direction):
        tick = Tick(instant, direction)
        self.ticks.append(tick)
        self.accumulated_charge += tick.CHARGE * tick.direction
        self.avg_current = self.accumulated_charge/(time()-self.start)

    def reset(self):
        self.ticks = []
        self.accumulated_charge = 0
        self.avg_current = 0
        self.start = time()

class Gui():
    def __init__(self):
        root = Tk()
        self.root = root

        self.time_elapsed = StringVar()
        self.number_of_ticks = StringVar()
        self.total_charge = StringVar()
        self.avg_current = StringVar()

        self.root.title("AMP-O-METER")

        self.mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        ttk.Label(self.mainframe, textvariable=self.time_elapsed).grid(column=1, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.number_of_ticks).grid(column=2, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.total_charge).grid(column=3, row=2, sticky=(W, E))
        ttk.Label(self.mainframe, textvariable=self.avg_current).grid(column=4, row=2, sticky=(W, E))

        ttk.Label(self.mainframe, text="Time elapsed:").grid(column=1, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total ticks:").grid(column=2, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Total charge (mC):").grid(column=3, row=1, sticky=W)
        ttk.Label(self.mainframe, text="Avg courrent (mA):").grid(column=4, row=1, sticky=W)

        # self.recharge_button = ttk.Button(self.mainframe, text="Recharge tick").grid(column=1, row=3, sticky=W)
        self.discharge_button = ttk.Button(self.mainframe, text="Reset")
        self.discharge_button.grid(column=4, row=3, sticky=W)

        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def run(self):
        self.root.mainloop()


class Controller():
    def __init__(self, polarity_pin=16, interrupt_pin=20):
        self.polarity_pin = polarity_pin
        self.interrupt_pin = interrupt_pin
        self.vio_pin = 21

        self.counter = Counter()
        self.gui = Gui()

        self.update_time_thread = Thread(target=self.update_time_elapsed, daemon=True)
        self.update_time_thread.start()

        # self.gui.recharge_button.bind("<Button>", self.add_tick)
        self.gui.discharge_button.bind("<Button>", self.reset)

        with open('history.csv', 'a') as file:
            file.write('time_absolute,time_relative,direction\n')


    def reset(self, *args):
        self.counter.reset()
        self.update_gui()

    def run(self):
        self.setup_probe()
        self.gui.run()


    def add_tick(self, directon=Tick.DISCHARGING):
        instant = time()
        self.counter.add_tick(instant, directon)
        self.update_gui()
        
        with open('history.csv', 'a') as file:
            file.write('{},{},{}\n'.format(time(), time()-self.counter.start, directon))

    def update_gui(self):
        self.gui.number_of_ticks.set(len(self.counter.ticks))
        self.gui.total_charge.set("{:8.5f}".format(self.counter.accumulated_charge))
        self.gui.avg_current.set("{:5.3f}".format(self.counter.avg_current))

        # TODO: add history list


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


    def probe_callback(self, *args):
        polarity = GPIO.input(self.polarity_pin)
        if polarity:
            polarity = Tick.RECHARGING
        else:
            polarity = Tick.DISCHARGING

        self.add_tick(polarity)



if __name__ == "__main__":
    controller = Controller()
    controller.run()
