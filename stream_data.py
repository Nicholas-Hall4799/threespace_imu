# A script to stream continuous data readings form the YOST
# 3-Space LX Evaluation Kit using Python 3.

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api
import time

# For testing, we have been using COM port 3
# Get a list of all LX type devices by using a filter to find only LX type devices.
# If the filter parameter is not used or set to null, all devices will be returned.
# 'getComPorts' returns a list containing the following device information:
# (COM port name, friendly name, 3-Space Sensor device type)
device_list = ts_api.getComPorts(filter=ts_api.TSS_FIND_LX)

# Take first (and presumably only) device.
com_port = device_list[0]
device = ts_api.TSLXSensor(com_port=com_port)

def getGyroDifference(data1, data2):
    differences = []
    for i in range(3):
        differences.append(abs(data1[i] - data2[i]))
    print("Differences between gryoscope readings: ")
    return differences

def getAccelDifference(data1, data2):
    differences = []
    for i in range(3,6):
        differences.append(abs(data1[i] - data2[i]))
    print("Differences between acceleration readings: ")
    return differences

def getCompDifference(data1, data2):
    differences = []
    for i in range(6,9):
        differences.append(abs(data1[i] - data2[i]))
    print("Differences between compass readings: ")
    return differences


while device is not None:
    # Begin streaming continuous data from our sensor.
    print("==================================================")
    print("Getting the current filtered tared quaternion orientation:")
    quat = device.getTaredOrientationAsQuaternion()
    if quat is not None:
        print(quat)

    print("==================================================")
    print("Getting the current corrected data:")
    data1 = device.getAllCorrectedComponentSensorData()

    print(len(data1))
    if data1 is not None:
        print("[%f, %f, %f] --Gyro\n"
              "[%f, %f, %f] --Accel\n"
              "[%f, %f, %f] --Comp" % data1)
    


    print("==================================================")
    print("Getting the raw sensor data:")
    data2 = device.getAllRawComponentSensorData()
    if data2 is not None:
        print("[%f, %f, %f] --Gyro\n"
              "[%f, %f, %f] --Accel\n"
              "[%f, %f, %f] --Comp" % data2)

    print("==================================================")

    print(getGyroDifference(data1, data2))
    print(getAccelDifference(data1, data2))
    print(getCompDifference(data1, data2))


    # Delay in output for readability.
    time.sleep(5)

# Now close the port.
device.close()