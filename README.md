#  Sammeln von Sensordaten mit Positionsbestimmung durch Dead Reckoning

Die im Rahmen einer Forschungsarbeit erstellten Programme dienen, um Umweltsensoren über ein standartisiertes Interface auszulesen und ihre Daten in eine InfluxDB Datenbank einzutragen. Ausgehend von der zu Beginn gemessenen GPS-Position wird mit einer inertial measurement unit (IMU) die Position zum Messzeitpunkt bestimmt und auch in die Datenbank eingetragen. Die Positionsbestimmung wird durch Dead Reckoning erzielt, einem Algorithmus der durch Integration von Beschleuningung und Winkelgeschwindgkeit die Position realativ zum Startpunkt bsetimmt. Es wird angenommen, dass das Gerät an der Wasseroberfläche startet, nach Norden zeigt und die ersten 3 Sekunden still steht. 

## Dead Reckoning
Dead Reckoning beruht auf dem Messen von Winkelgeschwindigkeit, dem Messen von Beschleunigung und einem bekannten Ausgangspunkt.
Die inertial measurement unit (IMU) misst die Beschleunigung auf drei Achsen in ihrem lokalen Koordinatensystem und misst die Winkelgschwindigkeit. Integriert man die Winkelgeschwindigkeit über die verstrichene Zeit, lässt sich augehend von der initialen Lage die aktuelle Lage der IMU berechnen. Durch das Anwenden von Rotationsmatrizen auf die Beschleunigung kann die Beschleunigung des Gerätes in Weltkoordinaten dargestellt werden. Von diesem Beschleunigungsvektor muss die erdrotationsbedingte Beschleunigung von 9,81 m/s^2 auf der z-Achse abgezogen werden. Integriert man die diese bereinigte Beschleunigung über die Zeit, erhält man die aktuelle Geschwindigkeit und durch eine weitere Integration die aktuelle Position des Gerätes.

## Geräte
- [Aceinna OpenIMU300ZI](https://openimu.readthedocs.io/en/latest/300ZI.html)
- [Drucksensor Ms5827](https://www.te.com/deu-de/product-CAT-BLPS0017.html)
- [Temperatur- und Drucksensor Tsys01](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FTSYS01%7FA%7Fpdf%7FEnglish%7FENG_DS_TSYS01_A.pdf%7FG-NICO-018)
- GPS-Tracker

## Installation
Der OpenIMU300ZI von Aceinna kann über über die vom Hersteller bereitgestellte [Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=platformio.aceinna-ide)  verschiedene Modelle zur Datenmessung und Navigation aufgespielt werden. Die zur Verfügungs stehenden Modelle haben teilweise Filter und Schntíttstellen für GPS mitinbegriffen. Das hier verwendete Modell gibt die rohen gemessenen Daten ohne Filter oder Navigation zurück, damit die gesamte Positionsberechnung außerhalb der IMU stattfindet. Modelle können unter der vom Hersteller bereitgestellten [Website](https://developers.aceinna.com/) simuliert werden.

Folgende Python3 Bibliotheken müssen mit den hier angegebenen Versionen installiert sein, um das Projekt laufen lassen zu können.
- influxdb = 5.3.1
- azure-common = 1.1.24
- azure-storage-blob = 2.1.0
- azure-storage-common = 2.1.0
- certifi = 2019.11.28
- cff = 1.13.2
- chardet = 3.0.4
- cryptography = 2.8
- idna = 2.8
-  isodate = 0.6.0
- msrest = 0.6.10
- oauthlib = 3.1.0
- pycparser = 2.19
- pyserial = 3.4
- python-dateutil = 2.8.1
- requests = 2.22.0
- requests-oauthlib = 1.3.0
- six = 1.13.0
- tornado = 6.0.3
- urllib3 = 1.25.7

## Externe Projekte
- [Treiber für OpenIMU300ZI](https://github.com/ROS-Aceinna/ros_openimu)  (das Projekt wurde editiert, um Aufrufe von ROS zu umgehen)
- [Treiber für Drucksensor ms5837](https://github.com/bluerobotics/ms5837-python)
- [Treiber für Temperatur- und Drucksensor tsys01](https://github.com/bluerobotics/tsys01-python)

## Verwendung
Um die Sensordaten mit Timestamp und Position zu sammeln, muss das Gerät nach Norden ausgerichtet werden und das Hauptskript `mainscript.py`gestartet werden. Die ersten drei Sekunden nach dem Start muss das Gerät ruhig gehalten werden, damit die Lage im raum bestimmt werden kann.
Die verwendeten Sensoren müssen in die Datei `sensorConfig.json` in folgendem Stile eingetragen werden.
##### Beispielhafter Eintrag für einen Sensor in json
```json
 {
    "sensor": "myfolder.mySensorScript",
    "class": "mySensorClass",
    "updateFrequency": 5,
    "measureTime": 1
  }
```
Dabei muss ein Pythonskript für jeden Sensorvorliegen, das eine Klasse mit drei Methoden beinhaltet:



```python
def init(self, updateFrequency, measureTime):
```
In dieser Methde wird die Instanz der KLasse erstellt und zum Beispiel die Verbindung zum Sensor hergestellt. `updateFrequency` gibt an, wie viele Sekunden zwischen zwei Messungen mindestens vergehen sollen. `measureTime` gibt an, wie lange eine Messung dauert. Beide Parameter werden aus dem Eintrag des Sensors in `sensorConfig.json` übernommen.

```python
def read(self):
``` 
Diese Funktion stößt die Messung an und gibt `True` zurück, falls die Messung erfolgreich ist. Andernfalls gibt sie `False` zurück.

```python
def getData(self):
``` 
Der zuletzt berechnete Wert wird hier abegrufen und muss den Namen des Sensors im Feld `measurement`, den Datenabnknutzer im Feld `tags`, den Timestamp im Feld `time` und in einem array namens `fields` alle Werte mit ihrem Name (wie z.B. Temparatur) enthalten. Der Timestamp muss der Form  `Jahr-Monat-Tag-Stunde:Minute:Sekunde` entsprechen
##### Beispielhafte Rückgabedaten für einen Drucksensor

```json
{
        "measurement": "mySensor",
        "tags": {
            "user": "root"
        },
        "time": measureTime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fields": {
            "pressure": str(self.sensor.pressure()),
        }
    }
```
Für die unter Geräte aufgeführten Sensoren sind bereits Skripte angelegt und die Sensoren in `sensorConfig.json`eingetragen.

## Skripte
Im Folgenden werden die Funktionsweisen der Skripte beschieben.
### Positionsbestimmung
```python
imuTracker.py
```
Diese Datei berechnet die Position ausgehend von Daten, die von der IMU bereitgestellt werden. Die dafür zuständiige Klasse ist  `LocationTracker`. Die Klasse wird mit Längen und Breitengraden eines GPS-Trackers initialisiert. 
Durch `LocationTracker(50.362998, 7.558995)` wird zum Beispiel als Startpunkt der Campus Koblenz festgelegt. 

Durch den direkten Aufruf des SKriptes werden rausch- und biasfreie Messdaten einer Wegstrecke eingegeben. Dabei fährt das Gerät ein Quadrat auf der xy-Ebene mit der Flläche 1 m^2 und geht einen Meter in die z-Achse nach oben und wieder nach unten. Damit endet der Weg am Startpunkt.

Hierbei handelt es sich um eine naive Implementierung eines Dead-Reckoning Algorithmus'. Es wird ein systeminterner Bias berechnet und berücksichtigt, Rauschen und Fehlmessungen werden jedoch nicht betrachtet. 

Folgende Funktionen werden verwendet:

```python
def rotate(self, accel):
```
Diese Funktion nimmt die Beschleunigung im Ortskoordinatensystem `accel` an und gibt sie in Weltkoordinaten zurück. Die aktuellen Winkel sind in den Klassenvariablen gespeichert.

```python
def updateAngles(self, rate, x_offset, y_offset, z_offset, deltaTime):
```
Die in der Klasse unter `self.angles` gespeicherten Winkel werden durch die neuen Daten geupdatet. Die zu Beginn berechneten Winkeloffsets werden von den gemssenen Winkelbeschleunigungen aus `rate` abgezogen und diese mit `deltaTime` multipliziert und auf die aktuellen Winkel addiert. Damit wird ein Integrationsschritt für die Winkel vorgenommen.
```python
def updateSpeed(self, accel, x_accelOff, y_accelOff, z_accelOff, timedelta):
```
Die in der Klasse unter `self.accel` gespeicherten Beschleunigungen in Weltkoordieaten werden durch die neuen Daten geupdatet. Die zu Beginn berechneten Beschleunigungsoffsets werden von der Beschleunigung `self.accelInwOrld` abgezogen und diese mit `timeDelta`multipliziert und auf die aktuellen Beschleunigung addiert. Die sich daraus ergebende Geschwindigkeit wird in `self.speed` gespeichert.`

```python
def updateLocation(self, obj):
```
Durch diese Funktion wird die Position geupdatet.
`obj` ist das Array, aus dem die Rohdaten der IMU ausgelesen werden.
| obj | Daten |
| ------ | ------ |
| obj[0] | Timestamp in Mikrosekunden |
| obj[1] | Beschelunigung auf x-Achse |
| obj[2] |  Beschelunigung auf y-Achse  |
| obj[3] | Beschelunigung auf z-Achse |
| obj[4] | Winkelbeschleunigung auf x-Achse |
| obj[5] | Winkelbeschleunigung auf y-Achse |
| obj[6] | Winkelbeschleunigung auf z-Achse |
| obj[7] | Magnetometer auf x-Achse |
| obj[8] | Magnetometer auf y-Achse |
| obj[9] | Magnetometer auf z-Achse |

Es wird angenommen, dass das Gerät in den ersten Sekunden still steht. Anhand der Daten aus den ersten Sekunden kann durch die erdrotationsbedingte statische Beschleunigung von 9,81 m/s^2 auf der z-Achse des Weltkoordinatensystems die Ausgangslage für die Winkel an der x-Achse und y-Achse bestimmt werden. Außerdem wird der Mittelwert der Beschleunigung und Winkelbeshleunigung aus dieser Zeit als statischer Offset angenommen, der bei jeder Berechnung abgezigen werden müssen, um den Bias des Systems auzugleichen. 

`updatLocation` updatet die Winkel, Beschlenigung, die Geschwindigkeit und die aktuelle Position des Gerätes.

```python
def getLocation(self):
```
Diese Funktion gibt die aktuelle Position als ein array der Form `[lon, lat, m]` zurück. Die Höhen- und Breitengrade und die Höhe des Gerätes n Metern werden angegeben.

### IMU Treiber
```python
imuDriver-py
```
Durch die in diesem Srikpt enthaltene Klasse, `OpenIMUDriver` kann über die von Aceinna zur Verfügung gestellte Bibliothek die Daten agesteuert werden.  Ruft man das Skript direkt auf, wird die Position dauerahaft durch dne oben beschriebenen `LocationTracker` anhand der Daten de IMU berechnet und das Ergebnis in Metern in der Datei `logFile.txt`gespeichert.

```python
 def readimu(self):
 ```
### Hauptskript
 Diese Funktion ruft die Daten von der IMU ab.
 
 ```python
mainscript.py
 ```
 
 Das Hauptskript liest eine Liste von verfügbaren Sensoren aus, erstellt eine Liste und bestimmt, welcher Sensor als nächstes ausgelesen wird. Die Daten werden mit Timestamp gespeichert. Zusätzlich wird die Position eingetragen, die durch einen mit einem GPS-Tracker initialisierten  `LocationTracker` berechnet wird.

## Auswertung

Die Positionsbestimmung ist ungefiltert. einem großen Rauschen unterworfen. Dies geht auch aus dem Paper [AI-IMU Dead-Reckoning](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9035481) von Martin Brossard , Axel Barrau und Silvère Bonnabel aus  _IEEE Transactions on Intelligent Vehicles 5.4 (2020): 585-595_  hervor. In den meisten Implemntationen werden die reinen Daten durch besipielsweise einen Kalmanfilter von Rauschen, Fehlmessungen und anderen Störungen bereinigt.
Da im Rahmen dieser Forschungsarbeit eine naive Positionsbestimmung ohne solche Filter vorgenommen wurde, divergieren die berechnete und die reale Position schnell voneinander.

In einem ersten Versuch wurde die Position des bewegungslosen Gerätes in zehn Versuchen für je 10 Sekunden berechnet. Der korrekte Wert wäre also 0 auf jeder Achse. Folgende Ergebnisse wurden zurückgegeben:

Versuch| x-Achse (m) | y-Achse (m) | z-Achse (m)
| ------| ------ | ------ | ------ |
1| 0,07 | 0,13 |-0,10
2| -0,09 | 0,03 |-0,03
3| 0,07 | -0,04 |-0,02
4| 0,05 | -0,03 |-0,03
5| -0,05 | -0,05 |-0,02
6| -0,14 | -0,05 |0,01
7| -0,08 | 0,03 |0,01
8| 0,04 | -0,06 |0,02
9| 0,03 | 0,5 |-0,01
10| 0,06 | 0,10 |-0,02

Die Divergenz wird bei Bewegung noch stärker. Nach einer Bewegung von wenigen Sekunden ist das Ergebnis um mehrere Meter inkorrekt.


