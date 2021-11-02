from influxdb import InfluxDBClient
import importlib
import json
import datetime 

class loader:

    def main(self):
        
        client = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
        client.create_database('example')
        client.switch_database('example')
        
        listOfSensors = self.loadAnything()
        listOfSensorsToRead = []
        listOfDadtaToGet = []

        while(True):          
           data = self.dataLogger(listOfSensors)

           #read all sensors that whose time it is
           #call read method, set lastRead variable to now, set time when data is available, add sensor to sensors that will have data soon
           for i in range(len(listOfSensors)):
             if(listOfSensors[i].lastRead + datetime.timedelta(milliseconds=listOfSensors[i].updateFrequency)  <= datetime.datetime.now()):
                 readSuccessful = listOfSensors[i].read()
                 listOfSensors[i].lastRead = datetime.datetime.now()
                 listOfSensors[i].dataReady = datetime.datetime.now() + datetime.timedelta(milliseconds=listOfSensors[i].measureTime)
                 listOfDadtaToGet.append(listOfSensors[i])
                 
                            #getdata from all available sensors
           for i in list(listOfDadtaToGet):
             if(i.dataReady <= datetime.datetime.now()):
               client.write_points(i.getData())
               print(i.getData())
               listOfDadtaToGet.remove(i)

     
           result = client.query('SELECT * FROM ms5837;')
           print(result)
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
       for i in range(len(json_array)): 
          module = importlib.import_module(json_array[i]['module'])
          print(json_array[i]['module'])
          class_ = getattr(module, json_array[i]['class'])
          print(json_array[i]['class'])
          instance = class_()
          list.append(instance)
          list[i].init(json_array[i]['updateFrequency'], json_array[i]['measureTime'])
       return list
