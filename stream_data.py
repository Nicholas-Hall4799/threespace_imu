# A script to stream continuous data readings form the YOST
# 3-Space LX Evaluation Kit using Python 3.

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api
import csv
import time

def get_port():
    found = False
    com_port = ""

    # Get all LX devices
    devices = ts_api.getComPorts(filter=ts_api.TSS_FIND_LX)

    if len(devices) > 0:
        # Take first (and presumably only) device.
        com_port = devices[0]
        found = True
    if found:
        print(f"Device found: {com_port}")
        return com_port
    else:
        print("No device was found.")
        return None

def get_csv_data(data, opened, file_name):
    ugly_time = time.time()
    time_stamp = time.ctime(ugly_time)
    row = { 
				'Time':time_stamp,'AccelCorrectedX' : data[0], 'AccelCorrectedY' : data[1], 'AccelCorrectedZ' : data[2],  
				'GyroCorrectedX' : data[3], 'GyroCorrectedY' : data[4], 'GyroCorrectedZ' : data[5],
				'Pitch' : data[6], 'Yaw' : data[7], 'Roll' : data[8]}
    if not opened:
        with open(file_name, 'w') as stream_data:
            field_names = ['Time','AccelCorrectedX','AccelCorrectedY','AccelCorrectedZ','GyroCorrectedX','GyroCorrectedY','GyroCorrectedZ', 'Pitch', 'Yaw', 'Roll']
            # Set field names in the CSV file
            writer = csv.DictWriter(stream_data, fieldnames = field_names)
            # Create header
            writer.writeheader()
            # Write data to file
            writer.writerow(row)
    else:
        with open(file_name, 'a') as stream_data:
            time_tuple = (time_stamp,)
            data_with_time = time_tuple + data
            writer = csv.writer(stream_data)
            writer.writerow(data_with_time)


def stream():
    streaming = True
    opened = False

    # These variables determine the filename scheme
	# Counter variable keeps track of number of csv files stored per session
    file_name = "imu_data.csv"

    port = get_port()
    # Connect sensor with the port
    device = ts_api.TSLXSensor(com_port = port)
    print(device)

    if device is not None:

        # Disable magnometer (compass)
        device.setCompassEnabled(enabled = False)
        # Set calibration mode to Scale/Bias mode
        device.setCalibrationMode(mode = 1)
        # Begin auto calibration of gyroscope
        device.beginGyroscopeAutoCalibration()
        # Set filter mode to Kalman
        device.setFilterMode(mode = 1)
        # Fix rate 
        device.setStreamingTiming(interval = 0, duration = 0xFFFFFFFF, delay = 0)
        # Start streaming
        device.startStreaming()
        device.startRecordingData()

        while streaming:

            # Set slots for tared quaternion and raw batch data - accel in units of g
            # gyro is in rad/sec
            device.setStreamingSlots( 
                slot0 = 'getCorrectedAccelerometerVector', 
                slot1 = 'getCorrectedGyroRate',
                slot2 = 'getTaredOrientationAsEulerAngles')
            print("==================================================")
            data = device.getLatestStreamData(1)[1]

            get_csv_data(data, opened, file_name)
            opened = True
            print(data)
            print("==================================================\n")
    
        device.stopStreaming()
        print("End of session")
        device.close()
    return None

def calculate_position():

    port = get_port()
    # Connect sensor with the port
    device = ts_api.TSLXSensor(com_port = port)

    euler_angles = device.getTaredOrientationAsEulerAngles
    print("Euler angles are as follows: " + euler_angles)
    pass
    
# def getGyroDifference(data1, data2):
#     differences = []
#     for i in range(3):
#         differences.append(abs(data1[i] - data2[i]))
#     print("Differences between gryoscope readings: ")
#     return differences

# def getAccelDifference(data1, data2):
#     differences = []
#     for i in range(3,6):
#         differences.append(abs(data1[i] - data2[i]))
#     print("Differences between acceleration readings: ")
#     return differences

# def getCompDifference(data1, data2):
#     differences = []
#     for i in range(6,9):
#         differences.append(abs(data1[i] - data2[i]))
#     print("Differences between compass readings: ")
#     return differences


# while device is not None:
#     # Begin streaming continuous data from our sensor.
#     print("==================================================")
#     print("Getting the current filtered tared quaternion orientation:")
#     quat = device.getTaredOrientationAsQuaternion()
#     if quat is not None:
#         print(quat)

#     print("==================================================")
#     print("Getting the current corrected data:")
#     data1 = device.getAllCorrectedComponentSensorData()

#     print(len(data1))
#     if data1 is not None:
#         print("[%f, %f, %f] --Gyro\n"
#               "[%f, %f, %f] --Accel\n"
#               "[%f, %f, %f] --Comp" % data1)
    


#     print("==================================================")
#     print("Getting the raw sensor data:")
#     data2 = device.getAllRawComponentSensorData()
#     if data2 is not None:
#         print("[%f, %f, %f] --Gyro\n"
#               "[%f, %f, %f] --Accel\n"
#               "[%f, %f, %f] --Comp" % data2)

#     print("==================================================")

#     print(getGyroDifference(data1, data2))
#     print(getAccelDifference(data1, data2))
#     print(getCompDifference(data1, data2))


#     # Delay in output for readability.
#     time.sleep(5)

# # Now close the port.
# device.close()

if __name__ == '__main__':
    try:
        stream()
    except KeyboardInterrupt:
        sys.exit()