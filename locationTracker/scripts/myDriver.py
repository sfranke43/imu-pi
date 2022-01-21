#!/usr/bin/env python3


import sys
import math
from time import time
from computeLocationNeu import LocationTracker


try:
    from ros_openimu.src.aceinna.tools import OpenIMU
except:  # pylint: disable=bare-except
    temp = (sys.path[0])
    temp2 = temp[0:(len(temp)-7)]
    sys.path.append(temp2 + 'src')
    #sys.path.append('./src')
    from aceinna.tools import OpenIMU


class OpenIMUros:
    def __init__(self):
        self.openimudev = OpenIMU()
        self.openimudev.startup()
        self.lt = LocationTracker(0,0)

    def close(self):
        self.openimudev.close()

    '''
    def readimu(self, packet_type):
        readback = self.openimudev.getdata(packet_type)
        return readback
    '''

    def readimu(self):
        readback = self.openimudev.getdata('z1')
        return readback

if __name__ == "__main__":


    seq = 0
    frame_id = 'OpenIMU'
    convert_rads = math.pi /180
    convert_tesla = 1/10000

    openimu_wrp = OpenIMUros()


    while True:
        #read the data - call the get imu measurement data
        readback = openimu_wrp.readimu()
        openimu_wrp.lt.updateLocation(readback)
        #publish the data m/s^2 and convert deg/s to rad/s
        print(readback)



        seq = seq + 1

    openimu_wrp.close()         # exit



