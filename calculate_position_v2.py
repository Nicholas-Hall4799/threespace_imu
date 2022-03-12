# A script to calculate the position of the 3-Space Sensor

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api
import numpy
import numpy.matlib
import matplotlib.pyplot as plt
from datetime import datetime
import csv
import time
import copy

# Function to connect to 3-Space Sensor
def initialize():
    # Function to identify the port being used by 3-Space Sensor
    def find_port():
        # devices = ts_api.getComPorts(filter=ts_api.TSS_FIND_LX)     # Get all LX devices
        devices = [ComInfo(com_port='COM3', friendly_name='USB Serial Device (COM3)', dev_type='LX')]
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
        device.tareWithCurrentOrientation()         # Tare with current orientation
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
        converted_array = accel_array*32.174
        converted_list = converted_array.tolist()
        return converted_list

def plot(x, y):
    plt.plot(x, y, linestyle= 'dashed')
    plt.title("Acceleration in X Direction")
    plt.xlabel("x axis")
    plt.ylabel("y axis")
    plt.ylim(-16, 16)
    plt.show()
    return None

def write_csv_data(data, opened, file_name, data_type):
    row = {data_type + 'X' : data[0][0], data_type + 'Y' : data[0][1], data_type + 'Z' : data[0][2], 'Time' : data[1]}
    if not opened:
        with open(file_name, 'w') as stream_data:
            field_names = [data_type + 'X',data_type + 'Y',data_type + 'Z', 'Time']
            writer = csv.DictWriter(stream_data, fieldnames = field_names)          # Set field names in the CSV file
            writer.writeheader()                                                    # Create header
            writer.writerow(row)                                                    # Write data to file
    else:
        with open(file_name, 'a') as stream_data:
            data_tuple = (data[0][0],data[0][1],data[0][2], data[1])
            writer = csv.writer(stream_data)
            writer.writerow(data_tuple)

def csv_to_list(file_name):
    with open(file_name, "rt") as infile:
        reader = csv.reader(infile)
        next(reader, None)  # skip the headers
        data_list = []
        for row in reader:
            # process each row
            data_list.append(row)
        for i in range(len(data_list)):
            if i < len(data_list):
                del data_list[i]
            i += 1
        for row in range(len(data_list)):
            for i in range(4):
                data_list[row][i] = float(data_list[row][i])
    return data_list

if __name__ == '__main__':
    try:
        device = initialize()
        device = calibrate(device)

        if device.getCompassEnabledState() == 0 and device.getAccelerometerRange() == 2:
            print("Compass is disabled and Accelerometer Range is +-8g.")
        else:
            print("Compass is enabled or Accelerometer Range is < 8g.")

        accel_file = "imu_accel_data.csv"
        velocity_file = "imu_velocity_data.csv"
        position_file = "imu_position_data.csv"
        opened = False

        acceleration_list = []
        velocity_list = []
        position_list = []

        acceleration = [[0,0,0], 0]
        velocity = [[0,0,0], 0]
        position = [[0,0,0], 0]

        velocity_list.append(velocity)
        position_list.append(position)

        index = 0
        notPressed = True

        while index < 1000:
            if index > 0:
            # Get current acceleration and append to list
                accel = list(device.getCorrectedAccelerometerVector())         # Accelerometer Values 
                accel[1] -= 1                                                  # Subtract 1g from Y-value
                accel = conversion(device, accel)                              # Convert from G's to Meters/Second²
            elif index == 0:
                accel = [0,0,0]
            time_stamp = time.time()                                       # Time stamp
            curr_acceleration = [accel, time_stamp]                        # List to store accelerometer values + time stamp
            acceleration_list.append(curr_acceleration)                    # Add to total acceleration list

            # print(f"Acceleration values are: {acceleration_list}")
            
            # Calculate velocity using acceleration
            if len(acceleration_list) > 1 and index > 0:                    # Wait until we've done one iteration
                for i in range(3):
                    if abs(acceleration_list[index][0][i]) < 3.2174:  #3.2174         # Threshold check to remove minute errors
                        acceleration_list[index][0][i] = 0.0
                    elif acceleration_list[index][0][i] > 135.1308:  #160.87
                        acceleration_list[index][0][i] = 135.1308      #160.87
                    elif acceleration_list[index][0][i] < -135.1308:  #160.87
                        acceleration_list[index][0][i] = -135.1308      #160.87
                    # Previous Velocity + (Current Acceleration + Previous Acceleration / 2 ) * (Current Time - Previous Time) 
                    velocity[0][i] = velocity_list[index-1][i] + ((acceleration_list[index][0][i] + acceleration_list[index-1][0][i])/2)*(acceleration_list[index][1] - acceleration_list[index-1][1])
            velocity[1] = acceleration_list[index][1]   
               
            write_csv_data(curr_acceleration, opened, accel_file, 'Acceleration')
            write_csv_data(velocity, opened, velocity_file, 'Velocity')
            velocity_list = csv_to_list(velocity_file)
            opened = True
            # if button_a.value:
            #     notPressed = True
            # else:                
            index += 1

        
            # opened = True

            # Correct with Rotation Matrix
            # rotation_array = numpy.array(get_rotation_matrix(device))          # Get rotation matrix as quanterions
            # rotation_matrix = rotation_array.reshape((3,3))
            # velocity_matrix = numpy.array(velocity[0])
            # corrected_velocity = numpy.matmul(rotation_matrix, velocity_matrix)
            # print(f"Corrected velocity is: {corrected_velocity}")
        index = 0
        opened = False
            # # TODO: Correct with Altimeter Values
        for i in range(len(velocity_list)):
            # Calculate position using velocity
            if index > 0:                    # Wait until we've done one iteration
                for i in range(3):
                    if abs(velocity_list[index][i]) < 3:               # Threshold check to remove minute errors
                        velocity_list[index][i] = 0.0
                    # Previous Position + (Current Velocity + Previous Velocity / 2 ) * (Current Time - Previous Time) 
                    position[0][i] = position_list[index-1][i] + ((velocity_list[index][i] + velocity_list[index-1][i])/2)*(velocity_list[index][3] - velocity_list[index-1][3])
            position[1] = velocity_list[index][3]
            # print(f"Position is: {position}")

            write_csv_data(position, opened, position_file, 'Position')
            position_list = csv_to_list(position_file)
            opened = True
            index += 1
        # TODO: Create and display plot of acceleration values
        # accel_x_values = []
        # length = []
        # for i in range(len(acceleration_list)):
        #     accel_x_values.append(acceleration_list[i][0][0])
        #     length.append(i)
        # plot(numpy.array(length), numpy.array(accel_x_values))

        device.close()
        grid_square = ""
        if position_list[-1][0] > -2500 and position_list[-1][0] <= -2250:
            grid_square += "A"
        elif position_list[-1][0] > -2250 and position_list[-1][0] <= -2000:
            grid_square += "B"
        elif position_list[-1][0] > -2000 and position_list[-1][0] <= -1750:
            grid_square += "C"
        elif position_list[-1][0] > -1750 and position_list[-1][0] <= -1500:
            grid_square += "D"
        elif position_list[-1][0] > -1500 and position_list[-1][0] <= -1250:
            grid_square += "E"
        elif position_list[-1][0] > -1250 and position_list[-1][0] <= -1000:
            grid_square += "F"        
        elif position_list[-1][0] > -1000 and position_list[-1][0] <= -750:
            grid_square += "G"        
        elif position_list[-1][0] > -750 and position_list[-1][0] <= -500:
            grid_square += "H"        
        elif position_list[-1][0] > -500 and position_list[-1][0] <= -250:
            grid_square += "I"        
        elif position_list[-1][0] > -250 and position_list[-1][0] <= 0:
            grid_square += "J"        
        elif position_list[-1][0] > 0 and position_list[-1][0] <= 250:
            grid_square += "K"        
        elif position_list[-1][0] > 250 and position_list[-1][0] <= 500:
            grid_square += "L"
        elif position_list[-1][0] > 500 and position_list[-1][0] <= 750:
            grid_square += "M"        
        elif position_list[-1][0] > 750 and position_list[-1][0] <= 1000:
            grid_square += "N" 
        elif position_list[-1][0] > 1000 and position_list[-1][0] <= 1250:
            grid_square += "O" 
        elif position_list[-1][0] > 1250 and position_list[-1][0] <= 1500:
            grid_square += "P" 
        elif position_list[-1][0] > 1500 and position_list[-1][0] <= 1750:
            grid_square += "Q" 
        elif position_list[-1][0] > 1750 and position_list[-1][0] <= 2000:
            grid_square += "R" 
        elif position_list[-1][0] > 2000 and position_list[-1][0] <= 2250:
            grid_square += "S" 
        elif position_list[-1][0] > 2250 and position_list[-1][0] <= 2500:
            grid_square += "T"
        if position_list[-1][2] > -2500 and position_list[-1][2] <= -2250:
            grid_square += "20"
        elif position_list[-1][2] > -2250 and position_list[-1][2] <= -2000:
            grid_square += "19"
        elif position_list[-1][2] > -2000 and position_list[-1][2] <= -1750:
            grid_square += "18"
        elif position_list[-1][2] > -1750 and position_list[-1][2] <= -1500:
            grid_square += "17"
        elif position_list[-1][2] > -1500 and position_list[-1][2] <= -1250:
            grid_square += "16"
        elif position_list[-1][2] > -1250 and position_list[-1][2] <= -1000:
            grid_square += "15"        
        elif position_list[-1][2] > -1000 and position_list[-1][2] <= -750:
            grid_square += "14"        
        elif position_list[-1][2] > -750 and position_list[-1][2] <= -500:
            grid_square += "13"        
        elif position_list[-1][2] > -500 and position_list[-1][2] <= -250:
            grid_square += "12"        
        elif position_list[-1][2] > -250 and position_list[-1][2] <= 0:
            grid_square += "11"        
        elif position_list[-1][2] > 0 and position_list[-1][2] <= 250:
            grid_square += "10"        
        elif position_list[-1][2] > 250 and position_list[-1][2] <= 500:
            grid_square += "9"
        elif position_list[-1][2] > 500 and position_list[-1][2] <= 750:
            grid_square += "8"        
        elif position_list[-1][2] > 750 and position_list[-1][2] <= 1000:
            grid_square += "7" 
        elif position_list[-1][2] > 1000 and position_list[-1][2] <= 1250:
            grid_square += "6" 
        elif position_list[-1][2] > 1250 and position_list[-1][2] <= 1500:
            grid_square += "5" 
        elif position_list[-1][2] > 1500 and position_list[-1][2] <= 1750:
            grid_square += "4" 
        elif position_list[-1][2] > 1750 and position_list[-1][2] <= 2000:
            grid_square += "3" 
        elif position_list[-1][2] > 2000 and position_list[-1][2] <= 2250:
            grid_square += "2" 
        elif position_list[-1][2] > 2250 and position_list[-1][2] <= 2500:
            grid_square += "1"
        print(grid_square)
    except KeyboardInterrupt:
        sys.exit()