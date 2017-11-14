import sys

# import fake_rpi
# sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi (GPIO)
# print("DEV VERSION!!! GPIO PINS DISABLED!!!")

if sys.version_info[0] < 3:
    print('You need to run this with Python 3')
    sys.exit(1)

import numpy as np
from amp_o_meter import *
from time import time
import json
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score


def create_controller(sensor):
    controller = Controller(
        create_csv=sensor["create_csv"],
        resistor_value=sensor["resistor_value"],
        ui_type="off",
        polarity_pin=sensor["polarity_pin"],
        interrupt_pin=sensor["interrupt_pin"],
        vio_pin=sensor["vio_pin"],
        ma_period=sensor["ma_period"]
    )
    controller.run()
    return controller


def calculate_lin_reg_coeffs(x, y):
    # x = [[1, 1], [1, 2], [1, 3], [1, 4]]
    # y = [10, 8, 6, 4]

    x = np.array(x)[np.newaxis].T
    y = np.array(y)
    regr = linear_model.LinearRegression()
    regr.fit(x, y)
    y_pred = regr.predict(x)
    print('Coefficients: y = {:.3g} * x + {:.3g}'.format(regr.coef_[0], regr.intercept_))
    print("Mean squared error: %.2f" % mean_squared_error(y, y_pred))
    print('Variance score: %.2f' % r2_score(y, y_pred))
    print()

    return {
        "a": regr.coef_[0],
        "b": regr.intercept_,
        "mean_squared_error": mean_squared_error(y, y_pred),
        "r_squared": r2_score(y, y_pred)
    }


if __name__ == "__main__":
    # int_pins = [21, 20, 16, 12, 25, 24, 23, 18]
    # pol_pins = [26, 19, 13, 6, 5, 22, 27, 17]

    int_pins = [21, 20]
    pol_pins = [26, 19]
    ema_period = 10

    sensor_list = []
    saved_tests = []
    test_counter = 0


    print("--- CALIBRATOR 2000 ---")
    test_timeout = input("Type timeout duration of each test in seconds: ")
    try:
        test_timeout = float(test_timeout)
    except:
        print("Could you please type a valid number the next time?")
        raise

    number_of_loops = input("How many loops in the sensor? : ")
    try:
        number_of_loops = float(number_of_loops)
        if number_of_loops == 1:
            resistor_value = 7.5
        elif number_of_loops == 2:
            resistor_value = 2.2
        elif number_of_loops == 4:
            resistor_value = 1.0
        else:
            raise

        print("Resistor selected: {}".format(resistor_value))

    except:
        print("Could you please type a valid number the next time?")
        raise


    for index, int_pin in enumerate(int_pins):
        sensor = {
            "id": "s"+str(index+1),
            "int_pin": int_pin,
            "create_csv": "off",
            "resistor_value": 7.5,
            "polarity_pin": pol_pins[index],
            "interrupt_pin": int_pin,
            "vio_pin": 4,
            "ma_period": ema_period
        }
        sensor["controller"] = create_controller(sensor)

        sensor_list.append(sensor)




    while True: # test loop: does all measurements
        print("\n----- New test ----------------------------------------------------------")
        print(" -- Type the real current value to begin a test")
        print(" -- Type F to finish tests and calculate calibration parameters")
        choice = input("F or value: ")

        try:
            real_current = float(choice)
            test_data = {
                "id": test_counter,
                "real_current": real_current
            }
            test_counter += 1
        except:
            if choice.upper() == "F":
                print("")
                break

        for sensor in sensor_list:
            sensor["controller"].reset()

        start = time()
        elapsed = 0
        done = False
        print("\n"*len(sensor_list))
        while not done:

            sleep(0.1)
            elapsed = time() - start
            done = True

            sys.stdout.write("\033[F"*len(sensor_list))
            for sensor in sensor_list:
                # the exact output you're looking for:
                elapsed_ticks = len(sensor["controller"].counter.ticks)
                done = done and (elapsed_ticks >= ema_period)

                sys.stdout.write("Sensor %s: [%-20s] %d%%\033[K\n" % (sensor["id"], '=' * min(int(elapsed_ticks / ema_period * 20), 20), min((elapsed_ticks / ema_period * 100), 100)))

            sys.stdout.flush()

            if time()-start > test_timeout:
                print(" --- Test timed out\n")
                break

        duration = time() - start
        print()

        # Time for the results!
        for sensor in sensor_list:
            sensor_id = sensor["id"]
            ticks_per_second = sensor["controller"].counter.ticks_per_second

            test_data["duration"] = duration
            test_data[sensor_id] = ticks_per_second
            print("   Sensor {}: {:.3f} ticks/second".format(sensor_id, ticks_per_second))
        print("")

        print(" -- Type again the real current value to begin a test")
        value = input("Value: ")
        test_data["real_current"] = (test_data["real_current"] + float(value))/2
        print(" -- Value for the real_current stored: {}".format(test_data["real_current"]))

        while True: # save data loop: waits for a valid response
            save_data = input("\nDo you want to save this test? [Y,n]: ")

            if save_data.upper() == 'Y' or save_data == '':
                saved_tests.append(test_data)
                print("Saved tests: {}".format(len(saved_tests)))
                break
            elif save_data.upper() == 'N':
                break
            else:
                print("Invalid option, please choose another")

    print("----- Interpolation ---------------------------------------------------------")
    # Calculate calibration coefficients
    # X axis is sensor data
    # Y axis is real current
    # y = f(x) -> y = a*x + b
    number_of_tests = len(saved_tests)
    for sensor in sensor_list:
        del sensor["controller"]

        y = []
        x = []

        for index, test in enumerate(saved_tests):
            x.append(test[sensor["id"]])
            y.append(test["real_current"])

        print("--- Sensor {} --------------------".format(sensor["id"]))
        regression_data = calculate_lin_reg_coeffs(x, y)
        sensor["regression_data"] = regression_data
        # print("Sensor {}: estimated_current = {} + {} * sensor_current".format(sensor["id"], regression_data["b"], regression_data["a"]))

    while True:  # save to file loop: waits for a valid response
        save_data = input("\nDo you want to save all data to a file? [Y,n]: ")

        if save_data.upper() == 'Y' or save_data == '':
            file_name = input("Please type the name of the file: ")
            file_name += ".json"
            with open(file_name, 'w') as json_file:
                all_data = {
                    "test_timeout": test_timeout,
                    "number_of_loops": number_of_loops,
                    "sensor_list": sensor_list,
                    "saved_tests": saved_tests
                }
                json.dump(all_data, json_file, indent=4, sort_keys=True)
                print("\nData saved to file successfully!")
                print("Bye bye!")
            break
        elif save_data.upper() == 'N':

            break
        else:
            print("Invalid option, please choose another")

    print("\n----- Calibration finished. Bye bye! --------------------------------------\n\n")
    GPIO.cleanup()
