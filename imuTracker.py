
import numpy as np
import sys
import time
import math
from gnss_ins_sim_master.gnss_ins_sim_master.demo_algorithms.free_integration import FreeIntegration

class LocationTracker:
    def __init__(self, lat, long):
        #assumption for starting position: all angles = 0 and IMU is at surface (z=0)
        self.angles = [0.0, 0.0, 0.0]
        self.deltaTime = 0.0
        self.lastReception_time = 0
        self.speed = [0.0, 0.0, 0.0]
        self.position = [0.0, 0.0, 0.0]
        self.lat = lat
        self.long = long


        self.calibrationStarted = False
        self.calibrationEnded = False
        self.xAccel_calibArray = []
        self.yAccel_calibArray = []
        self.zAccel_calibArray = []
        self.xAngle_calibArray = []
        self.yAngle_calibArray = []
        self.zAngle_calibArray = []
        self.x_accelOffset = 0
        self.y_accelOffset = 0
        self.z_accelOffset = 0
        self.x_angleOffset = 0
        self.y_angleOffset = 0
        self.z_angleOffset = 0
        #comparison to established tracker
        #self.compareAlgo = FreeIntegration(np.repeat(0, 9), earth_rot=False)


    def rotate(self, accel):
        rotation_x = np.array([[1, 0, 0],
                               [0, np.cos(np.deg2rad(self.angles[0])), -np.sin(np.deg2rad(self.angles[0]))],
                               [0, np.sin(np.deg2rad(self.angles[0])), np.cos(np.deg2rad(self.angles[0]))]])
        rotation_y = np.array([[np.cos(np.deg2rad(self.angles[1])), 0, np.sin(np.deg2rad(self.angles[1]))],
                               [0, 1, 0],
                               [-np.sin(np.deg2rad(self.angles[1])), 0, np.cos(np.deg2rad(self.angles[1]))]])
        rotation_z = np.array([[np.cos(np.deg2rad(self.angles[2])), -np.sin(np.deg2rad(self.angles[2])), 0],
                               [np.sin(np.deg2rad(self.angles[2])), np.cos(np.deg2rad(self.angles[2])), 0],
                               [0, 0, 1]])

        #get accelaration data in local coordinates
        accel = np.array( [accel[0], accel[1], accel[2]])
        #print(rotation_x)
        #print(rotation_y)
        #print(rotation_z)
        #multiply roatation matrices to local accelaration
        accelWithZ = np.dot(rotation_z, accel)
        accelWithZY = np.dot(rotation_y, accelWithZ)
        return np.dot(rotation_x, accelWithZY)

    def updateSpeed(self, accel, x_accelOff, y_accelOff, z_accelOff, timedelta):
        #compute roatation matrices for bringing accelartion data to world coordinates
        #angles are given in deg and must be transformed to rad
        self.accelInWorld = self.rotate(accel)

        #subtract offset from acceleration
        print(self.accelInWorld)
        self.accelInWorld[0] = self.accelInWorld[0] - x_accelOff
        self.accelInWorld[1] = self.accelInWorld[1] - y_accelOff
        self.accelInWorld[2] = self.accelInWorld[2] - z_accelOff

        #self.accelInWorld = np.dot(accel, R.from_euler('zyx', [self.z_angle, self.y_angle, self.x_angle], degrees=True))


        #integrate to speed
        self.speed[0] += (self.accelInWorld[0]) * timedelta
        self.speed[1] += (self.accelInWorld[1]) * timedelta
        self.speed[2] += (self.accelInWorld[2]) * timedelta

    #deltaTime in seconds
    def updateAngles(self, rate, x_offset, y_offset, z_offset, deltaTime):
        #integrate and subtract offset from angles
        self.angles[0] = (self.angles[0] + ((rate[0] - x_offset) * deltaTime)) % 360
        self.angles[1] = (self.angles[1] + ((rate[1] - y_offset) * deltaTime)) % 360
        self.angles[2] = (self.angles[2] + ((rate[2] - z_offset) * deltaTime)) % 360

    def updateLocation(self, obj):
        if self.calibrationStarted == False:
            self.calibrationStart = time.time()
            self.calibrationStarted = True
        if int(time.time() - self.calibrationStart) > 3 and self.calibrationEnded == False:

            self.angles[0] = np.arcsin(np.mean(self.xAccel_calibArray) / 9.81) * 180 / np.pi
            self.angles[1] = np.arctan2(np.mean(self.yAccel_calibArray), np.mean(self.zAccel_calibArray)) * 180 / np.pi
            print(int(time.time() - self.calibrationStart))
            # self.x_angle = np.arctan2(np.mean(self.yAccel_calibArray), np.mean(self.zAccel_calibArray)) * 180/np.pi
            # self.y_angle = np.arctan2(-np.mean(self.xAccel_calibArray), np.sqrt(np.mean(self.yAccel_calibArray)*np.mean(self.yAccel_calibArray) + np.mean(self.zAccel_calibArray)*np.mean(self.zAccel_calibArray))) * 180/np.pi
            print(self.angles[0])
            print(self.angles[1])

            for i in range(len(self.xAccel_calibArray)):
                calibAccelInWorld = self.rotate([self.xAccel_calibArray[i], self.yAccel_calibArray[i], self.zAccel_calibArray[i]])
                self.xAccel_calibArray[i] = calibAccelInWorld[0]
                self.yAccel_calibArray[i] = calibAccelInWorld[1]
                self.zAccel_calibArray[i] = calibAccelInWorld[2]

            self.x_angleOffset = np.mean(self.xAngle_calibArray)
            self.y_angleOffset = np.mean(self.yAngle_calibArray)
            self.z_angleOffset = np.mean(self.zAngle_calibArray)
            self.x_accelOffset = np.mean(self.xAccel_calibArray)
            self.y_accelOffset = np.mean(self.yAccel_calibArray)
            self.z_accelOffset = np.mean(self.zAccel_calibArray)
            self.calibrationEnded = True
            print("___________________Offset:___________________")
            print(self.x_accelOffset)
            print(self.y_accelOffset)
            print(self.z_accelOffset)
            print(self.x_angleOffset)
            print(self.y_angleOffset)
            print(self.z_angleOffset)
            print("_____________________________________________")
            #time.sleep(3)

        if self.lastReception_time == 0:
            timedelta = 0
        else:
            timedelta = (obj[0] - self.lastReception_time) / 1000000
        self.lastReception_time = obj[0]
        self.updateAngles([obj[4], obj[5], obj[6]], self.x_angleOffset, self.y_angleOffset, self.z_angleOffset, timedelta)
        self.updateSpeed([obj[1], obj[2], obj[3]], self.x_accelOffset, self.y_accelOffset, self.z_accelOffset, timedelta)

        if self.calibrationEnded == False:
            self.angles = [0, 0 ,0]
            self.speed = [0, 0 ,0]
            self.position = [0, 0, 0]

            self.xAccel_calibArray.append(obj[1])
            self.yAccel_calibArray.append(obj[2])
            self.zAccel_calibArray.append(obj[3])
            self.xAngle_calibArray.append(obj[4])
            self.yAngle_calibArray.append(obj[5])
            self.zAngle_calibArray.append(obj[6])


        #integrate to position
        self.position[0] += self.speed[0] * timedelta
        self.position[1] += self.speed[1] * timedelta
        self.position[2] += self.speed[2] * timedelta
        #output for debugging


        sys.stdout.write("Angular rate\n%0.2f\n" % obj[4])
        sys.stdout.write("%0.2f\n" % obj[5])
        sys.stdout.write("%0.2f\n" % obj[6])
        sys.stdout.write("Angle\n%0.2f\n" % self.angles[0])
        sys.stdout.write("%0.2f\n" % self.angles[1])
        sys.stdout.write("%0.2f\n" % self.angles[2])
        sys.stdout.write("Accel\n%0.2f\n" % obj[1])
        sys.stdout.write("%0.2f\n" % obj[2])
        sys.stdout.write("%0.2f\n" % obj[3])
        sys.stdout.write("AccelInWorld\n%0.2f\n" % self.accelInWorld[0])
        sys.stdout.write("%0.2f\n" % self.accelInWorld[1])
        sys.stdout.write("%0.2f\n" % (self.accelInWorld[2]))
        #sys.stdout.write(self.compareAlgo.run([1, obj[0], obj[1:4], obj[4:7]]))
        if math.isclose(self.accelInWorld[0] * self.accelInWorld[0] +  self.accelInWorld[1] *self.accelInWorld[1] +self.accelInWorld[2] * self.accelInWorld[2], obj[1]*obj[1] + obj[2]*obj[2] + obj[3]*obj[3] - 9.81*9.81):
            print("accelInwOrld is same size as accel")
        else:
            print("accelInwOrld is NOT same size as accel")
        sys.stdout.write("Speed\n%0.2f\n" % self.speed[0])
        sys.stdout.write("%0.2f\n" % self.speed[1])
        sys.stdout.write("%0.2f\n" % self.speed[2])
        sys.stdout.write("Position\n%0.2f\n" % self.position[0])
        sys.stdout.write("%0.2f\n" % self.position[1])
        sys.stdout.write("%0.2f\n\n\r" % self.position[2])
        sys.stdout.write("%0.8f\n\n\r" % obj[0])
        sys.stdout.write("timedelta: %0.8f\n\r" % timedelta)
        sys.stdout.flush()
        #time.sleep(3)




    def getLocation(self):
        r_earth = 6371
        new_latitude = self.lat + (self.position[1] / r_earth) * (180 / np.pi)
        new_longitude = self.long + (self.position[0]  / r_earth) * (180 / np.pi) / np.cos(self.lat * np.pi / 180)
        np.set_printoptions(suppress=True)
        return np.array([new_longitude, new_latitude, self.position[2]])

if __name__ == "__main__":
    loc = LocationTracker(0,0)
    loc.updateLocation([0,0,0,0,0,0,0])
    time.sleep(5)
    loc.updateLocation([5000000, 0, 0, 0, 0, 0, 0])
    loc.updateLocation([6000000, 10, 0, 10, 0, 0, 0])
    loc.updateLocation([7000000, -8, 0, -10, 0, 0, 0])
    loc.updateLocation([8000000, 0, 0, 0, 0, 0, 90])
    loc.updateLocation([9000000, 10, 0, 0, 0, 0, 0])
    loc.updateLocation([10000000, -10, 0, 0, 0, 0, 0])
    loc.updateLocation([11000000, 0, 0, -10, 0, 0, 90])
    loc.updateLocation([12000000, 10, 0, 10, 0, 0, 0])
    loc.updateLocation([13000000, -10, 0, 0, 0, 0, 0])
    loc.updateLocation([14000000, 0, 0, 0, 0, 0, 90])
    loc.updateLocation([15000000, 10, 0, 0, 0, 0, 0])
    loc.updateLocation([16000000, -10, 0, 0, 0, 0, 0])






