# A script to calculate the position of the 3-Space Sensor

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api
import numpy
import numpy.matlib
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Function to connect to 3-Space Sensor
def initialize():
    # Function to identify the port being used by 3-Space Sensor
    def find_port():
        devices = ts_api.getComPorts(filter=ts_api.TSS_FIND_LX)     # Get all LX devices
        sensor_port = devices[0]                                    # Take first (and presumably only) device.
        return sensor_port

    print("Connecting to the 3-Space Sensor...")
    try:
        sensor = ts_api.TSLXSensor(com_port=find_port())
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror))
    except ValueError:
        print("Could not convert data.", traceback.format_exc())
    except:
        print("Unexpected error:", sys.exc_info()[0], traceback.format_exc())
        print("Could not connect to 3-Space Sensor on {0} or error in setting configuration - closing".format(find_port()))
        return 1

    print("Succesfully connected to 3-Space Sensor on port {0}.".format(find_port()))

    return sensor       # Connect sensor with the port

# Function to set proper modes for 3-Space Sensor and begin auto-calibration
def calibrate(device):
    if device is not None:
        device.setCompassEnabled(enabled = False)   # Disable magnometer (compass)
        device.setCalibrationMode(mode = 1)         # Set calibration mode to Scale/Bias mode
        device.beginGyroscopeAutoCalibration()      # Begin auto calibration of gyroscope
        device.setFilterMode(mode = 1)              # Set filter mode to Kalman
        device.setAccelerometerRange(2)             # Set acceleration range to +-2g
        return device

def get_rotation_matrix(device):
    if device is not None:

        rotation_matrix = device.getTaredOrientationAsRotationMatrix()

        return rotation_matrix

# Function to convert Acceleration list from G's to Meters/Second²
def conversion(device, accel_list):
    if device is not None:
        accel_array = numpy.array(accel_list)
        converted_array = accel_array*9.8066
        converted_list = converted_array.tolist()
        return converted_list

def plot(x, y):
    plt.plot(x, y, linestyle= 'dashed')
    plt.title("Acceleration in X Direction")
    plt.xlabel("x axis")
    plt.ylabel("y axis")
    plt.show()
    return None

if __name__ == '__main__':
    try:
        device = initialize()
        device = calibrate(device)

        if device.getCompassEnabledState() == 0 and device.getAccelerometerRange() == 2:
            print("Compass is disabled and Acceleratometer Range is +-8g.")
        else:
            print("Compass is enabled or Acceleratometer Range is < 8g.")

        acceleration_list = []
        velocity_list = []
        position_list = []

        acceleration = []
        velocity = [[0,0,0], 0]
        position = []

        velocity_list.append(velocity)

        index = 0

        while index < 10000:

            # Get current acceleration and append to list
            accel = list(device.getCorrectedLinearAccelerationInGlobalSpace())       # Accelerometer Values
            # Convert from G's to Meters/Second²
            conversion(device, accel)

            accel_time = time.time()                                            # Time stamp
            curr_acceleration = [accel, accel_time]                      # List to store accelerometer values + time stamp
            acceleration_list.append(curr_acceleration)                         # Add to total acceleration list
            # print(f"Acceleration values are: {acceleration_list}")
            # time.sleep(0.2)
            # Calculate velocity using acceleration
            for i in range(3):
                if len(acceleration_list) > 1 and index > 0:
                    if acceleration_list[index][0][i] < abs(0.05):
                        acceleration_list[index][0][i] = 0.0
                    velocity[0][i] = velocity_list[index-1][0][i] + (acceleration_list[index][0][i] + acceleration_list[index-1][0][i])/2*(acceleration_list[index][1] - acceleration_list[index-1][1])
                    velocity_list.append(velocity)

            index += 1

            # Correct with Rotation Matrix
            rotation_array = numpy.array(get_rotation_matrix(device))          # Get rotation matrix as quanterions
            rotation_matrix = rotation_array.reshape((3,3))
            velocity_matrix = numpy.array(velocity[0])
            corrected_velocity = numpy.matmul(rotation_matrix, velocity_matrix)
            print(f"Corrected velocity is: {corrected_velocity}")

            # TODO: Correct with Altimeter Values
            # TODO: Get Position

        # TODO: Creat and display plot of acceleration values
        accel_x_values = []
        length = []
        print(acceleration_list)
        print(len(acceleration_list))
        for i in range(len(acceleration_list)):
            accel_x_values.append(acceleration_list[i][0][0])
            length.append(i)
        plot(numpy.array(length), numpy.array(accel_x_values))
        
    except KeyboardInterrupt:
        sys.exit()