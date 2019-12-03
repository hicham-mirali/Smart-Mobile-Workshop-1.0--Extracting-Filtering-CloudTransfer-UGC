#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import serial
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ser = serial.Serial(
	port='/dev/ttyUSB1',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1
)

try:
	ser.isOpen()
except Exception, e:
	print "error open serial port: " + str(e)
	exit()

f=open("releveUGC.txt","a+")

ser.write("FLASH\r")
FlashFlag = ser.readlines()
if ("<FLASH  -  US_ONCF 1.5>" in str(FlashFlag)):
	print "Fenetre Flash Ouverte"
	ser.write("DBD\r")
	DBDFlag = ser.readlines()
	if ("Situazione record DataBase Diagnostico" in str(DBDFlag)):
		print "Fenetre DBD ouverte"
		ser.write("DLALL\r")
		tempEstimeBrutA = ser.readline()
		tempEstimeBrutB = ser.readline()
		print tempEstimeBrutB
		tempEstimeSplit = tempEstimeBrutB.split()
		tempEstime = tempEstimeSplit[6]
		print "Temps Estime : "+ tempEstime +"secondes"
		timeout = 40
		timeout_start = time.time()
		ser.write("\r")
		while(time.time() < (timeout_start + timeout)):
			releve = ser.readline()
			f.write(releve)
			print "Envoi en cours"
		f.close()
		print "Relevé réalisé avec succès"
		ser.write('\x03')
		time.sleep(0.5)
		ser.write('\x03')
		time.sleep(0.5)
		ser.write('\x03')
	else:
		print "Impossible d'ouvrir fenetre DBD"
		ser.write('\x03')
		time.sleep(0.5)
		ser.write('\x03')
else : 
	print "Impossible d'ouvrir fenetre Flash"
	ser.write('\x03')

#Envoi du relevé par e-mail
subject = "Relevé US"
body = "Veuillez trouver ci-joint le relevé de l'US comme demandé."
sender_email = "XXX"
receiver_email = "XXX"
password = "eracugc0!"

# Create a multipart message and set headers
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject

# Add body to email
message.attach(MIMEText(body, "plain"))

filename = "releveUGC.txt"  # In same directory as script

# Open PDF file in binary mode
with open(filename, "rb") as attachment:
    # Add file as application/octet-stream
    # Email client can usually download this automatically as attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())

# Encode file in ASCII characters to send by email    
encoders.encode_base64(part)

# Add header as key/value pair to attachment part
part.add_header(
    "Content-Disposition",
    "attachment; filename=releveUGC.txt",
)

# Add attachment to message and convert message to string
message.attach(part)
text = message.as_string()

# Log in to server using secure context and send email

mailserver = smtplib.SMTP('smtp.gmail.com',587)
# identify ourselves to smtp gmail client
mailserver.ehlo()
# secure our email with tls encryption
mailserver.starttls()
# re-identify ourselves as an encrypted connection
mailserver.ehlo()
mailserver.login(sender_email, password)

mailserver.sendmail(sender_email, receiver_email, text)

mailserver.quit()

print "Email envoyé"
