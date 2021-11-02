#!/usr/bin/python
from SensorTsys01 import tsys01
import datetime
import json
from datetime import date

class hotHotHot(object):
    
    def init(self, updateFrequency, measureTime):
        self.sensor = tsys01.TSYS01() # Default I2C bus is 1 (Raspberry Pi 3)
        self.measureTime = measureTime
        self.updateFrequency = updateFrequency
        self.lastRead = datetime.datetime.now()
        self.dataReady = datetime.datetime.now()
        if self.sensor.init() == True:
            return True
        else:
            return False


    def read(self):
        if self.sensor.read() == True:
            return True
        else:
            return False   


    def getData(self):
        st = datetime.datetime.now()
        data = [{
        "measurement": "tsys01",
        "tags": {
            "user": "root"
        },
        "time": st.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": {
            "temp" : str(self.sensor.temperature())
        }
    }]
        return data
          



