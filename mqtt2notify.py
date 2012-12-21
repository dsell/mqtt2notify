#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# mqtt2notify
#	Provides growl notification messages from an mqtt broker.
#


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


import os
import sys
import logging
import signal
import time
import pynotify
import mosquitto
import socket
from config import Config


CLIENT_NAME = "mqtt2notify[" + socket.gethostname() + "]"
CLIENT_VERSION = "0.6"
CLIENT_BASE = "/clients/" + CLIENT_NAME
MQTT_TIMEOUT = 60	#seconds
LOGFORMAT = '%(asctime) - 15s %(message)s'
LOGFILE = "/var/log/mqtt-growl.log"


#TODO might want to add a lock file
#TODO  need to deal with no config file existing!!!
#read in configuration file
homedir = os.path.expanduser("~")
f = file(homedir + '/.mqtt2notify.conf')
cfg = Config(f)
MQTT_HOST = cfg.MQTT_HOST
MQTT_PORT = cfg.MQTT_PORT
WATCH_TOPICS = cfg.WATCH_TOPICS


mqtt_connected = False


#define what happens after connection
def on_connect( self, obj, rc):
	global mqtt_connected
	mqtt_connected = True
	print "Connected"
	n = pynotify.Notification ( "MQTT Connected." )
	n.show ()
	mqttc.publish ( CLIENT_BASE + "/status" , "connected", 1, 1 )
	mqttc.publish( CLIENT_BASE + "/version", CLIENT_VERSION, 1, 1 )
	for topic in WATCH_TOPICS:
		mqttc.subscribe( topic, 2 )
	mqttc.subscribe( CLIENT_BASE + "ping", 2)


def on_disconnect( self, obj, rc ):
	pass


#On recipt of a message create a pynotification and show it
def on_message( self, obj, msg):
	if (( msg.topic == CLIENT_BASE + "ping" ) and ( msg.payload == "request" )):
		mqttc.publish( CLIENT_BASE + "ping", "response", qos = 1, retain = 0 )
	else:
		if not ( msg.retain ):
			n = pynotify.Notification (msg.topic, msg.payload)
			n.show ()


def mqtt_disconnect():
	global mqtt_connected
	print "Disconnecting..."
	mqttc.disconnect()
	if ( mqtt_connected ):
		mqtt_connected = False 
		print "MQTT Disconnected"
		n = pynotify.Notification ( "MQTT disconnected." )
		n.show ()


def mqtt_connect():

	rc = 1
	while ( rc ):
		print "Attempting connection..."
		mqttc.will_set( CLIENT_BASE + "/status", "disconnected_", 1, 1)

		#define the mqtt callbacks
		mqttc.on_message = on_message
		mqttc.on_connect = on_connect
#		mqttc.on_disconnect = on_disconnect

		#connect
		rc = mqttc.connect( MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT )
		if rc != 0:
			logging.info( "Connection failed with error code $s, Retrying in 30 seconds.", rc )
			print "Connection failed with error code ", rc, ", Retrying in 30 seconds." 
			time.sleep(30)
		else:
			print "Connect initiated OK"

def cleanup(signum, frame):
	mqtt_disconnect()
	sys.exit(signum)


#register with notification system
pynotify.init("mqtt-growl")

#create an mqtt client
mqttc = mosquitto.Mosquitto( CLIENT_NAME )

#trap kill signals including control-c
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)


def main_loop():
	global mqtt_connected
	mqttc.loop(10)
	while True:
		if ( mqtt_connected ):
			rc = mqttc.loop(10)
			if rc != 0:	
				mqtt_disconnect()
				print rc
				print "Stalling for 20 seconds to allow broker connection to time out."
				time.sleep(20)
				mqtt_connect()
				mqttc.loop(10)
		pass


mqtt_connect()
main_loop()
