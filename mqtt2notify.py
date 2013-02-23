#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# mqtt2notify
#    Provides growl notification messages from an mqtt broker.
#


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


APPNAME = "mqtt2notify"
VERSION = "0.10"
WATCHTOPIC = "/raw/" + APPNAME + "/command"

import pynotify
from daemon import Daemon
from mqttcore import MQTTClientCore
from mqttcore import main
import config


class MyMQTTClientCore(MQTTClientCore):
    def __init__(self, appname, clienttype):
        MQTTClientCore.__init__(self, appname, clienttype)
        self.clientversion = VERSION
        self.watchtopic = self.cfg.WATCH_TOPICS
        #register with notification system
        pynotify.init(APPNAME)

    def on_connect(self, mself, obj, rc):
        MQTTClientCore.on_connect(self, mself, obj, rc)
        n = pynotify.Notification("MQTT Connected.")
        n.show()
        for topic in self.watchtopic:
            self.mqttc.subscribe(topic, qos=2)

    def on_disconnect(self, mself, obj, rc):
        MQTTClientCore.on_disconnect(self, mself, obj, rc)
        print "MQTT Disconnected"
        n = pynotify.Notification("MQTT disconnected.")
        n.show()

    def on_message(self, mself, obj, msg):
        MQTTClientCore.on_message(self, mself, obj, msg)
        if not (msg.retain):
            n = pynotify.Notification(msg.topic, msg.payload)
            n.show()


class MyDaemon(Daemon):
    def run(self):
        mqttcore = MyMQTTClientCore(APPNAME, clienttype="type2")
        mqttcore.main_loop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/' + APPNAME + '.pid')
    main(daemon)
