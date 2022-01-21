
import numpy as np
import sys
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import math

class LocationTracker:
    def __init__(self, x_position, y_position):
        #assumption for starting position: all angles = 0 and IMU is at surface (z=0)
        self.x_angle = 0.0
        self.y_angle = 0.0
        self.z_angle = 0.0
        self.deltaTime = 0.0
        self.lastReception_time = 0
        self.speed_x = 0
        self.speed_y = 0
        self.speed_z = 0
        self.x_position = x_position
        self.y_position = y_position
        self.z_position = 0


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
    def updateSpeed(self, xAccel, yAccel, zAccel, x_accelOff, y_accelOff, z_accelOff, timedelta):
        #compute roatation matrices for bringing accelartion data to world coordinates
        #angles are given in deg and must be transformed to rad
        rotation_x = np.matrix([[1, 0, 0],
                               [0, np.cos(np.deg2rad(self.x_angle)), -np.sin(np.deg2rad(self.x_angle))],
                               [0, np.sin(np.deg2rad(self.x_angle)), np.cos(np.deg2rad(self.x_angle))]])
        rotation_y = np.matrix([[np.cos(np.deg2rad(self.y_angle)), 0, np.sin(np.deg2rad(self.y_angle))],
                               [0, 1, 0],
                               [-np.sin(np.deg2rad(self.y_angle)), 0, np.cos(np.deg2rad(self.y_angle))]])
        rotation_z = np.matrix([[np.cos(np.deg2rad(self.z_angle)), -np.sin(np.deg2rad(self.z_angle)), 0],
                               [np.sin(np.deg2rad(self.z_angle)), np.cos(np.deg2rad(self.z_angle)), 0],
                               [0, 0, 1]])
        '''
        #older version without converting to rad
        rotation_x = np.matrix([[1, 0, 0],
                        [0, np.cos((self.x_angle)), -np.sin((self.x_angle))],
                        [0, np.sin((self.x_angle)), np.cos((self.x_angle))]])
        rotation_y = np.matrix([[np.cos((self.y_angle)), 0, np.sin((self.y_angle))],
                        [0, 1, 0],
                        [-np.sin((self.y_angle)), 0, np.cos((self.y_angle))]])
        rotation_z = np.matrix([[np.cos((self.z_angle)), -np.sin((self.z_angle)), 0],
                        [np.sin((self.z_angle)), np.cos((self.z_angle)), 0],
                        [0, 0, 1]])
        '''
        #get accelaration data in local coordinates
        accel = np.matrix( [xAccel, yAccel, zAccel])
        print(rotation_x)
        print(rotation_y)
        print(rotation_z)
        #multiply roatation matrices to local accelaration
        accelWithX = np.matmul(rotation_x, accel.transpose())
        accelWithXY = np.matmul(rotation_y, accelWithX)
        self.accelInWorld = np.matmul(rotation_z, accelWithXY)
        #subtract offset from acceleration
        print(self.accelInWorld)
        self.accelInWorld[0, 0] = self.accelInWorld[0, 0]  - x_accelOff
        self.accelInWorld[1, 0] = self.accelInWorld[1, 0] - y_accelOff
        self.accelInWorld[2, 0] = self.accelInWorld[2, 0] - z_accelOff


        #integrate to speed
        self.speed_x += (self.accelInWorld[0,0]) * timedelta
        self.speed_y += (self.accelInWorld[1,0]) * timedelta
        self.speed_z += (self.accelInWorld[2,0]) * timedelta

    def updateLocation(self, obj):
        if(self.calibrationStarted == False):
            self.calibrationStart = time.time()
            self.calibrationStarted = True
        if(time.time() - self.calibrationStart > 5 and self.calibrationEnded == False):
            self.calibrationEnded = True
            self.x_accelOffset = np.mean(self.xAccel_calibArray)
            self.y_accelOffset = np.mean(self.yAccel_calibArray)
            self.z_accelOffset = np.mean(self.zAccel_calibArray)
            self.x_angleOffset = np.mean(self.xAngle_calibArray)
            self.y_angleOffset = np.mean(self.yAngle_calibArray)
            self.z_angleOffset = np.mean(self.zAngle_calibArray)
            print(self.xAccel_calibArray)
        if (self.calibrationEnded == False):
            self.x_angle = 0
            self.y_angle = 0
            self.z_angle = 0
            self.speed_x = 0
            self.speed_y = 0
            self.speed_z = 0
            self.x_position = 0
            self.y_position = 0
            self.z_position = 0
            self.xAccel_calibArray.append(obj[1])
            self.yAccel_calibArray.append(obj[2])
            self.zAccel_calibArray.append(obj[3])
            self.xAngle_calibArray.append(obj[4])
            self.yAngle_calibArray.append(obj[5])
            self.zAngle_calibArray.append(obj[6])
        timedelta = (obj[0] - self.lastReception_time) / 1000000
        self.lastReception_time = obj[0]
        self.updateAngles(obj[4], obj[5], obj[6], self.x_angleOffset, self.y_angleOffset, self.z_angleOffset, timedelta)
        self.updateSpeed(obj[1], obj[2], obj[3], self.x_accelOffset, self.y_accelOffset, self.z_accelOffset, timedelta)

        #integrate to position
        self.x_position += self.speed_x * timedelta
        self.y_position += self.speed_y * timedelta
        self.z_position += self.speed_z * timedelta
        #output for debugging

        print("___________________Offset:___________________")
        print(self.x_accelOffset)
        print(self.y_accelOffset)
        print(self.z_accelOffset)
        print(self.x_angleOffset)
        print(self.y_angleOffset)
        print(self.z_angleOffset)
        print("_____________________________________________")
        sys.stdout.write("Anglular rate\n%0.2f\n" % obj[4])
        sys.stdout.write("%0.2f\n" % obj[5])
        sys.stdout.write("%0.2f\n" % obj[6])
        sys.stdout.write("Angle\n%0.2f\n" % self.x_angle)
        sys.stdout.write("%0.2f\n" % self.y_angle)
        sys.stdout.write("%0.2f\n" % self.z_angle)
        sys.stdout.write("Accel\n%0.2f\n" % obj[1])
        sys.stdout.write("%0.2f\n" % obj[2])
        sys.stdout.write("%0.2f\n" % obj[3])
        sys.stdout.write("AccelInWorld\n%0.2f\n" % self.accelInWorld[0,0])
        sys.stdout.write("%0.2f\n" % self.accelInWorld[1,0])
        sys.stdout.write("%0.2f\n" % (self.accelInWorld[2,0]))
        if math.isclose(self.accelInWorld[0,0] * self.accelInWorld[0,0] +  self.accelInWorld[1,0] *self.accelInWorld[1,0] +self.accelInWorld[2,0] * self.accelInWorld[2,0], obj[1]*obj[1] + obj[2]*obj[2] + obj[3]*obj[3] - 9.81*9.81):
            print("accelInwOrld is same size as accel")
        else:
            print("accelInwOrld is NOT same size as accel")
        sys.stdout.write("Speed\n%0.2f\n" % self.speed_x)
        sys.stdout.write("%0.2f\n" % self.speed_y)
        sys.stdout.write("%0.2f\n" % self.speed_z)
        sys.stdout.write("Position\n%0.2f\n" % self.x_position)
        sys.stdout.write("%0.2f\n" % self.y_position)
        sys.stdout.write("%0.2f\n\n\r" % self.z_position)
        sys.stdout.write("%0.8f\n\n\r" % obj[0])
        sys.stdout.write("timedelta: %0.8f\n\r" % timedelta)
        sys.stdout.flush()


    #deltaTime in seconds
    def updateAngles(self, x_rate, y_rate, z_rate, x_offset, y_offset, z_offset, deltaTime):
        #integrate and subtract offset from angles
        self.x_angle = (self.x_angle + ((x_rate - x_offset) * deltaTime)) % 360
        self.y_angle = (self.y_angle + ((y_rate - y_offset) * deltaTime)) % 360
        self.z_angle = (self.z_angle + ((z_rate - z_offset) * deltaTime)) % 360




