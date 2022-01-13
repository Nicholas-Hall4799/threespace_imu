# A script to calculate the position of the 3-Space Sensor

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api
import math
import numpy
import scipy.integrate as integrate
import csv
import time

def initialize():
    def find_port():
        # Get all LX devices
        devices = ts_api.getComPorts(filter=ts_api.TSS_FIND_LX)
        # Take first (and presumably only) device.
        sensor_port = devices[0]
        
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

    # Connect sensor with the port
    return sensor

def calibrate(device):
    if device is not None:
        # Disable magnometer (compass)
        device.setCompassEnabled(enabled = False)
        # Set calibration mode to Scale/Bias mode
        device.setCalibrationMode(mode = 1)
        # Begin auto calibration of gyroscope
        device.beginGyroscopeAutoCalibration()
        # Set filter mode to Kalman
        device.setFilterMode(mode = 1)
        # Set acceleration range to +-8g
        device.setAccelerometerRange(2)

        return device

def calculate_position(device):
    init_velocity = 0
    init_accel = 0

    def get_accel():
        accel = device.getCorrectedAccelerometerVector()
        time_stamp = time.ctime(time.time())
        data = [accel, time_stamp]
        return data

    euler_angle = device.getTaredOrientationAsEulerAngles()
    # Rotation around the side-to-side axis in radians. (Theta)
    pitch = euler_angle[0]
    # Rotation around the vertical axis in radians. (Psi)
    yaw = euler_angle[1]
    # Rotation around the front-to-back axis in radians. (Phi)
    roll = euler_angle[2]

    # Rotation Matrix Calculations
    m_11 = math.cos(roll) * math.cos(pitch)
    m_12 = math.sin(yaw) * math.cos(pitch)
    m_13 = -1 + math.sin(pitch)
    m_21 = (math.cos(yaw) * math.sin(pitch) * math.sin(roll)) - (math.sin(roll) * math.cos(roll))
    m_22 = (math.sin(yaw) * math.sin(pitch) * math.sin(roll)) + (math.cos(yaw) * math.cos(roll))
    m_23 = math.cos(pitch) * math.sin(yaw)
    m_31 = (math.cos(yaw) * math.sin(pitch) * math.cos(roll)) + (math.sin(yaw) + math.sin(roll))
    m_32 = (math.sin(yaw) + math.sin(pitch) + math.cos(roll)) - (math.cos(yaw) * math.sin(roll))
    m_33 = math.cos(pitch) * math.cos(roll)

    rotation_matrix = numpy.array([[m_33, m_32, m_31], [m_23, m_22, m_21], [m_13, m_12, m_11]])

    numpy.transpose(rotation_matrix)

    #dx_dt, dy_dt, dz_dt = 0

    print(f"Roll: {roll}")
    print(f"Pitch: {pitch}")
    print(f"Yaw: {yaw}")
    print(f"Euler angles are as follows: {euler_angle}")
    print(f"Rotation Matrix: \n {rotation_matrix}")
    print(get_accel())


if __name__ == '__main__':
    try:
        device = initialize()
        device = calibrate(device)
        if device.getCompassEnabledState() == 0 and device.getAccelerometerRange() == 2:
            print("Compass is disabled and Acceleratometer Range is +-8g.")
        else:
            print("Compass is enabled or Acceleratometer Range is < 8g.")

        calculate_position(device)
    except KeyboardInterrupt:
        sys.exit()
