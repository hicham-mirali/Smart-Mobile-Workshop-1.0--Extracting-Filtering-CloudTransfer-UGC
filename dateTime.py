#! /usr/bin/env python
# -*- coding: utf-8 -*-

import time
import serial
from datetime import datetime


ser = serial.Serial(
	port='/dev/ttyUSB0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

currentTime = datetime.now()
currentTimeStr = currentTime.strftime("%d/%m/%y %H:%M:%S")


ser.write("DATAORA\r")
time.sleep(0.5)
ser.write(currentTimeStr+"\r")
time.sleep(0.5)
ser.write('\x03')
print ("Date et heure mis à jour")
