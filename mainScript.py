from influxdb import InfluxDBClient
import importlib
import json
from imuDriver import OpenIMUDriver
import datetime 

class loader:

    def main(self):
        client = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
        client.create_database('example')
        client.switch_database('example')
        #variables for keeping track of the location
        self.locationCalledLastTime = datetime.datetime.now()
        listOfSensors = self.loadAnything()
        listOfSensorsToRead = []
        listOfDataToGet = []
        self.location = self.gpsTracker.getPosition()
        self.imu = OpenIMUDriver(self.location[0], self.location[1])

        while(True):
            readback = self.imu.readimu()
            self.imu.lt.updateLocation(readback)
            if self.locationCalledLastTime + datetime.timedelta(milliseconds=self.locationUpdateRate)  <= datetime.datetime.now():
                self.location = self.imu.lt.getLocation()
                self.locationCalledLastTime = datetime.datetime.now()
            data = self.dataLogger(listOfSensors)

            #read all sensors that whose time it is
            #call read method, set lastRead variable to now, set time when data is available, add sensor to sensors that will have data soon
            for i in range(len(listOfSensors)):

                if(listOfSensors[i].lastRead + datetime.timedelta(milliseconds=listOfSensors[i].updateFrequency)  <= datetime.datetime.now()):
                    readSuccessful = listOfSensors[i].read()
                    listOfSensors[i].lastRead = datetime.datetime.now()
                    listOfSensors[i].dataReady = datetime.datetime.now() + datetime.timedelta(milliseconds=listOfSensors[i].measureTime)
                    listOfDataToGet.append(listOfSensors[i])
                 
            #getdata from all available sensors
            for i in list(listOfDataToGet):
                if(i.dataReady <= datetime.datetime.now()):
                    toDataBase = i.getData()
                    toDataBase[0]['fields'].update({'gps': self.location})
                    print(toDataBase)
                    client.write_points(toDataBase)
                    listOfDataToGet.remove(i)


        #client.drop_database('example')
        
        
    def dataLogger(self, list):


       result = []
       for i in range(len(list)):
          list[i].read()
          return list[i].getData()
          result.append(list[i].getData())
       
       return result
    
    
    def loadAnything(self):
        input_file = open ('sensorConfig.json')
        json_array = json.load(input_file)
        list = []
     
        for iterator in range(len(json_array)):
            #add all sensors (i.e. not class for getting location) to list of sensors
            print(json_array[iterator])
            print(iterator)
            if not (json_array[iterator].get('sensor') is None):
                module = importlib.import_module(json_array[iterator]['sensor'])
                print(json_array[iterator]['sensor'])
                class_ = getattr(module, json_array[iterator]['class'])
                print(json_array[iterator]['class'])
                instance = class_()
                list.append(instance)
                list[len(list)-1].init(json_array[iterator]['updateFrequency'], json_array[iterator]['measureTime'])
             
            else:
                module = importlib.import_module(json_array[iterator]['module'])
                print(json_array[iterator]['module'])
                class_ = getattr(module, json_array[iterator]['class'])
                print(json_array[iterator]['class'])
                instance = class_()
                self.gpsTracker = instance
                self.gpsTracker.init()
                self.locationUpdateRate = json_array[iterator]['updateFrequency']
        return list
#
if __name__ == "__main__":
    l = loader()
    l.main()