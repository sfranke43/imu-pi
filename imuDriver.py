#!/usr/bin/env python3


import sys
from imuTracker import LocationTracker


try:
    from library.locationTracker.src.aceinna.tools import OpenIMU
except:  # pylint: disable=bare-except
    temp = (sys.path[0])
    temp2 = temp[0:(len(temp)-7)]
    sys.path.append(temp2 + 'src')
    #sys.path.append('./src')
    from library.locationTracker.src.aceinna.tools import OpenIMU


class OpenIMUDriver:
    def __init__(self, x_start, y_start):
        self.openimudev = OpenIMU()
        self.openimudev.startup()
        self.lt = LocationTracker(x_start,y_start)

    def close(self):
        self.openimudev.close()



    def readimu(self):
        readback = self.openimudev.getdata('z1')
        return readback

if __name__ == "__main__":
    frame_id = 'OpenIMU'
    openimu_wrp = OpenIMUDriver(0,0)
    f = open("logFile.txt", "w")

    while True:
        #read the data - call the get imu measurement data
        readback = openimu_wrp.readimu()
        openimu_wrp.lt.updateLocation(readback)
        #publish the data m/s^2 and convert deg/s to rad/s
        print(readback)
        f.write(repr(openimu_wrp.lt.position))
        f.write("\n")
    f.close()


    openimu_wrp.close()         # exit



