#!/usr/bin/python
from SensorMs5837 import ms5837
import datetime
import json
from datetime import date

class underPressure(object):
    
    
    
    def init(self, updateFrequency, measureTime):
        self.sensor = ms5837.MS5837_30BA() # Default I2C bus is 1 (Raspberry Pi 3)
        #sensor = ms5837.MS5837_30BA(0) # Specify I2C bus
        #sensor = ms5837.MS5837_02BA()
        #sensor = ms5837.MS5837_02BA(0)
        #sensor = ms5837.MS5837(model=ms5837.MS5837_MODEL_30BA, bus=0) # Specify model and bus
        self.measureTime = measureTime
        self.updateFrequency = updateFrequency
        self.lastRead = datetime.datetime.now()
        self.dataReady = datetime.datetime.now()
        if self.sensor.init() == True:
            return True
        else:
            return False


    def read(self):
        #update the time when data is ready to be read
        if self.sensor.read() == True:
            return True
        else:
            return False   


    def getData(self):
        #data = {}
        st = datetime.datetime.now()
        data = [{
        "measurement": "ms5837",
        "tags": {
            "user": "root"
        },
        "time": st.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": {
            "pressure": str(self.sensor.pressure()),
            "temp" : str(self.sensor.temperature())
        }
    }]
        
        #data["measurement"] = "ms5837"
        #data["mytime"] = st.strftime("%Y-%m-%dT%H:%M:%SZ")
        #data["pressure"] = str(self.sensor.pressure())
        #data["temp"] = str(self.sensor.temperature())
        #json_data = json.dumps(data)
        return data
          


