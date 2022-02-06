from gpsdclient import GPSDClient

class gps:
   def init(self):
       self.gpsClient = GPSDClient(host="127.0.0.1")
       return True
    
# get your data as json strings:
   def getPosition(self):
       for result in self.gpsClient.dict_stream(convert_datetime=True):
          if result["class"] == "TPV":
             #print("Latitude: %s" % result.get("lat", "n/a"), " Longitude: %s" % result.get("lon", "n/a"))
             return [result.get("lat", "n/a"), result.get("lon", "n/a"), 0]


