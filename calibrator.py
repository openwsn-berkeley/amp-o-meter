import sys
import numpy as np
import json
import numpy as np
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score

# import fake_rpi
# sys.modules['RPi'] = fake_rpi.RPi     # Fake RPi (GPIO)
# print("DEV VERSION!!! GPIO PINS DISABLED!!!")

if sys.version_info[0] < 3:
    print('You need to run this with Python 3')
    sys.exit(1)

from amp_o_meter import *
from time import time


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

    return {
        "a": regr.coef_[0],
        "b": regr.intercept_,
        "mean_squared_error": mean_squared_error(y, y_pred),
        "r_squared": r2_score(y, y_pred)
    }


if __name__ == "__main__":
    int_pins = [21, 20, 16, 12, 25, 24, 23, 18]
    pol_pins = [26, 19, 13,  6,  5, 22, 27, 17]
    sensor_list = []
    saved_tests = []
    test_counter = 0

    for index, int_pin in enumerate(int_pins):
        sensor_list.append({
            "id": "s"+str(index),
            "int_pin": int_pin,
            "create_csv": "off",
            "resistor_value": 7.5,
            "polarity_pin": pol_pins[index],
            "interrupt_pin": int_pin,
            "vio_pin": 4,
            "ma_period": 0
        })

    print("--- CALIBRATOR 2000 ---")
    duration = input("Type the duration of each test in seconds: ")
    try:
        duration = float(duration)
    except:
        print("Could you please type a valid number the next time?")
        raise

    while True: # test loop: does all measurements
        print("\n----- New test --------------------------------")
        print(" -- Type the real current value to begin a test")
        print(" -- Type F to finish tests and calculate calibration parameters")
        choice = input("Choice: ")

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
            sensor["controller"] = create_controller(sensor)

        start = time()
        elapsed = 0
        while duration - elapsed > 0:

            sleep(0.1)
            elapsed = time() - start

            sys.stdout.write('\r')
            # the exact output you're looking for:
            sys.stdout.write("[%-20s] %d%%" % ('=' * int(elapsed / duration * 20), elapsed / duration * 100))
            sys.stdout.flush()

        for sensor in sensor_list:
            sensor["controller"].clean_gpio()
            sensor_id = sensor["id"]
            avg_current = sensor["controller"].counter.avg_current
            del sensor["controller"]

            test_data[sensor_id] = avg_current
            print("   Sensor {}: {} mA".format(sensor_id, avg_current))
        print("")

        while True: # save data loop: waits for a valid response
            save_data = input("Do you want to save this test? [Y,n]: ")

            if save_data.upper() == 'Y' or save_data == '':
                saved_tests.append(test_data)
                print("Saved tests: {}".format(len(saved_tests)))
                break
            elif save_data.upper() == 'N':
                break
            else:
                print("Invalid option, please choose another")

    # Calculate calibration coefficients
    # X axis is sensor data
    # Y axis is real current
    # y = f(x) -> y = a*x + b
    number_of_tests = len(saved_tests)
    for sensor in sensor_list:
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
