#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import dateTime
import paho.mqtt.client as mqtt
import ssl 
import jwt , json
import datetime
from parsargs import parse_command_line_args
import time
import random
import logging
import ast
import re 
import serial


ser = serial.Serial(
	port='/dev/ttyUSB0',
	baudrate=9600,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout = 0.1
)

try:
	ser.isOpen()
except Exception, e:
	print "error opent serial port: " + str(e)
	exit()

mqtt.Client.connected_flag=False
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.CRITICAL)

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 32

# Whether to wait with exponential backoff before publishing.
should_backoff = False

# [START iot_mqtt_jwt]
def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         private_key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            An MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the private_key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
            algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)
# [END iot_mqtt_jwt]


def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', mqtt.connack_string(rc))
    # After a successful connect, reset backoff time and stop backing off.
    global should_backoff
    global minimum_backoff_time
    should_backoff = False
    minimum_backoff_time = 1


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print('on_disconnect', error_str(rc))

    # Since a disconnect occurred, the next loop iteration will wait with
    # exponential backoff.
    global should_backoff
    should_backoff = True


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print('on_publish')


def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    payload = str(message.payload)
    print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            payload, message.topic, str(message.qos)))


def get_client(
        project_id, cloud_region, registry_id, device_id, private_key_file,
        algorithm, ca_certs, mqtt_bridge_hostname, mqtt_bridge_port):
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    client_id= "projects/{}/locations/{}/registries/{}/devices/{}".format(
                               project_id,
                               cloud_region,
                               registry_id,
                               device_id)
    print(client_id)
    client = mqtt.Client(client_id)

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
            username='unused',
            password=create_jwt(
                    project_id, private_key_file, algorithm))

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    client.connect(mqtt_bridge_hostname, mqtt_bridge_port)
    
        

    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = '/devices/{}/config'.format(device_id)

    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=1)

    # The topic that the device will receive commands on.
    mqtt_command_topic = '/devices/{}/commands/#'.format(device_id)

    # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
    print('Subscribing to {}'.format(mqtt_command_topic))
    client.subscribe(mqtt_command_topic, qos=0)

    return client


def mqtt_device_demo(args):
    global minimum_backoff_time
    global MAXIMUM_BACKOFF_TIME

    # Publish to the events or state topic based on the flag.
    sub_topic = 'events' if args.message_type == 'event' else 'state'

    mqtt_topic = '/devices/{}/{}'.format(args.device_id, sub_topic)

    jwt_iat = datetime.datetime.utcnow()
    jwt_exp_mins = args.jwt_expires_minutes
    client = get_client(
        args.project_id, args.cloud_region, args.registry_id,
        args.device_id, args.private_key_file, args.algorithm,
        args.ca_certs, args.mqtt_bridge_hostname, args.mqtt_bridge_port)

# Publish num_messages mesages to the MQTT bridge once per second.
    #for i in range(1, args.num_messages + 1):
        # Process network events.
    client.loop()

    if should_backoff:
	# If backoff time is too large, give up.
    	if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
    		print('Exceeded maximum backoff time. Giving up.')
       		#break
	
	# Otherwise, wait and connect again.
    	delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
    	print('Waiting for {} before reconnecting.'.format(delay))
    	time.sleep(delay)
    	minimum_backoff_time *= 2
    	client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    lastSent = ''
    while(True):
	data = [""] * 8
	firstRun = True
	ser.write('\x03')
	time.sleep(0.2)
	ser.write("FLASH\r")
	flashFlag=ser.readlines()

	if ("<FLASH  -  US_ONCF 1.5>" in str(flashFlag)):
		print "Flash window opened."
		ser.write("DBD\r")
		dbdFlag = ser.readlines()

		if ("Situazione record DataBase Diagnostico" in str(dbdFlag)):
			print "DBD window opened"
			ser.write("LAST\r")
			time.sleep(0.2)
			ser.readline()
			i = 0
			for i in range (8):
				data[i] = ser.readline()
				print "data[i] : " + data[i]
				print "Last Sent : " + lastSent
				if data[i] == lastSent :
					print "Data from previous itteration reached"
					ser.write('\x03')
					time.sleep(0.2)
					ser.write('\x03')
					break

				diagnosticCode = data[i].split()
				if (len(diagnosticCode) > 3 ):
					if ((diagnosticCode[2] == 'A') or (diagnosticCode[2] == 'D')):
						date = diagnosticCode[0] + " " + diagnosticCode [1]
						codeBrut = diagnosticCode[3]
						codeSplit = codeBrut.split('-')
						code = codeSplit[0]
						if (diagnosticCode[2] == 'A'):
							state = "ON"
						if (diagnosticCode[2] == 'D'):
							state = "OFF"
						voiture = "1"
						equi = "UGC"
						jsonData= {
							"Code" : code ,
							"Voiture" : voiture,
							"equi"  : equi,
							"date"  : date,
							"State" : state
						}
	
						payload = json.dumps(jsonData)
                				print('Publishing message :' ) + payload 
                				seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
                				if seconds_since_issue > 60 * jwt_exp_mins:
                     					print('Refreshing token after {}s').format(seconds_since_issue)
                     					jwt_iat = datetime.datetime.utcnow()
                     					client = get_client(
                     					args.project_id, args.cloud_region,
                     					args.registry_id, args.device_id, args.private_key_file,args.algorithm, args.ca_certs, args.mqtt_bridge_hostname,
                     					args.mqtt_bridge_port)
        					# Publish "payload" to the MQTT topic. qos=1 means at least once
        					# delivery. Cloud IoT Core also supports qos=0 for at most once
        					# delivery.
                				client.publish(mqtt_topic, payload, qos=1)

						if firstRun:
							lastSent = data[i]
							firstRun = False
        					# Send events every second. State should not be updated as often
                				time.sleep(1 if args.message_type == 'event' else 5)
	
						ser.write('\x03')
						time.sleep(0.2)
						ser.write('\x03')
					else : 
						print("Irrelevant data")
						ser.write('\x03')
						time.sleep(0.2)
						ser.write('\x03')
		else:
			print "Unable to open DBD window"
			ser.write('\x03')
	else : 
		print "Unable to open Flash window"


def main():
    args = parse_command_line_args()
    mqtt_device_demo(args)

if __name__ == '__main__':
   main() 

