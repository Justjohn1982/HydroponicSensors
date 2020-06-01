#!/usr/bin/env python

import os
from time import sleep
import yaml
config = yaml.safe_load(open("config.yml"))

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
TDS_Relay = config["tds-relay"]
GPIO.setup(TDS_Relay, GPIO.OUT)
GPIO.output(TDS_Relay, GPIO.HIGH)
sleep(2)
GPIO.output(TDS_Relay, GPIO.LOW)
sleep(2)
GPIO.output(TDS_Relay, GPIO.HIGH)
