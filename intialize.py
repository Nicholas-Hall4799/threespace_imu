# A script to initialize a COM connection with Embedded LX Sensor using Python 3.

# Utilize the Python API for the sensor, the threespace_api.
from threespace_api import *
import threespace_api as ts_api

global sensor
global sensor_port


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
    sensor.close()

if __name__ == '__main__':
    initialize()