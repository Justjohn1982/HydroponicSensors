#!/usr/bin/env python

import os
from time import sleep
import yaml
config = yaml.safe_load(open("config.yml"))

import Adafruit_DHT
import board
import busio
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
TDS_Relay = config["tds-relay"]
GPIO.setup(TDS_Relay, GPIO.OUT)
GPIO.output(TDS_Relay, GPIO.HIGH)
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate(config["firebase-certificate"])
firebase_admin.initialize_app(cred)

db = firestore.client()

# Water temperature setup
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

water_temp_sensor = config["water-temperature-device"]

def read_water_temp_raw():
    f = open(water_temp_sensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_water_temp():
    lines = read_water_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        sleep(0.2)
        lines = read_water_temp_raw()

    temp_result = lines[1].find('t=')

    if temp_result != -1:
        temp_string = lines[1].strip()[temp_result + 2:]
        temp = float(temp_string) / 1000.0
        return temp

water_temperature = read_water_temp()
print('Water Temperature: ' + str(water_temperature))
sleep(1)

# Ambient stuff here
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = config["ambient-sensor"]
humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
if humidity is not None and temperature is not None:
    print("Room Temperature={0:0.2f}*C  Humidity={1:0.2f}%".format(temperature, humidity))
else:
    print("Failed to retrieve data from humidity sensor")

# Analogue stuff here
ads = ADS.ADS1115(i2c)

#pH
ph = AnalogIn(ads, ADS.P0)
pHValue=(config["ph"]["m"]*ph.voltage+config["ph"]["b"])
print('pH: '+str(pHValue))

#TDS
tds = AnalogIn(ads, ADS.P1)
def read_tds():
    tdsValues = []
    GPIO.output(TDS_Relay, GPIO.LOW)
    sleep(5)
    for x in range(7):
        tdsValues.append((133.42*tds.voltage*tds.voltage*tds.voltage - 255.86*tds.voltage*tds.voltage + 857.39*tds.voltage)*0.5)
        sleep(1)
    GPIO.output(TDS_Relay, GPIO.HIGH)
    tdsValues.sort()
    return mean(tdsValues[1,-1])
tdsValue = read_tds()
print('TDS (ppm): ' + str(tdsValue))

#Store it on firestore
doc_ref = db.collection(u'kitchen').document()
doc_ref.set({
    u'air_temp': temperature,
    u'humidity': humidity,
    u'created': datetime.datetime.now(),
    u'ph': pHValue,
    u'tds': tdsValue,
    u'water_level': 0,
    u'water_flow': 0,
    u'water_temp': water_temperature
})
