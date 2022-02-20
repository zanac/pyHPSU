#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [MQTT]
# BROKER = localhost
# PORT = 1883
# USERNAME = 
# PASSWORD = 
# CLIENTNAME = rotex_hpsu
# PREFIX = rotex

import configparser
import requests
import sys
import os
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt



class export():
    hpsu = None

    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.hpsu = hpsu
        self.logger = logger
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            self.config.read(self.config_file)
        else:
            sys.exit(os.EX_CONFIG)

        # object to store entire MQTT config section
        self.mqtt_config = self.config['MQTT']
        self.brokerhost = self.mqtt_config.get('BROKER', 'localhost')
        self.brokerport = self.mqtt_config.getint('PORT', 1883)
        self.clientname = self.mqtt_config.get('CLIENTNAME', 'rotex')
        self.username = self.mqtt_config.get('USERNAME', None)
        if self.username is None:
            self.logger.error("Username not set!!!!!")
        self.password = self.mqtt_config.get('PASSWORD', "NoPasswordSpecified")
        self.prefix = self.mqtt_config.get('PREFIX', "")
        self.qos = self.mqtt_config.getint('QOS', 0)
        # every other value implies false
        self.retain = self.mqtt_config.get('RETAIN', "NOT TRUE") == "True"
        # every other value implies false
        self.addtimestamp = self.mqtt_config.get('ADDTIMESTAMP', "NOT TRUE") == "True"

        self.logger.info("configuration parsing complete")   

        # no need to create a different client name every time, because it only publish
        # so adding the PID at the end of the client name ensures every process have a
        # different client name only for readability on broker and troubleshooting
        self.clientname += "-" + str(os.getpid())

        self.logger.info("creating new mqtt client instance: " + self.clientname)
        self.client=mqtt.Client(self.clientname)
        self.client.on_publish = self.on_publish
        if self.username:
           self.client.username_pw_set(self.username, password=self.password)
        self.client.enable_logger()

    
    def on_publish(self,client,userdata,mid):
        self.hpsu.logger.debug("mqtt output plugin data published, mid: " + str(mid))

    def pushValues(self, vars=None):

        self.logger.info("connecting to broker: " + self.brokerhost + ", port: " + str(self.brokerport))
        self.client.connect(self.brokerhost, port=self.brokerport)

        #self.msgs=[]
        for r in vars:
            msgs=[]
            if self.prefix:
                ret=self.client.publish(self.prefix + "/" + r['name'],payload=r['resp'], qos=int(self.qos))
                topic=self.prefix + "/" + r['name']
            else:
                ret=self.client.publish(r['name'],payload=r['resp'], qos=int(self.qos))
                topic=r['name']
            msg={'topic':topic,'payload':r['resp'], 'qos':self.qos, 'retain':False}

        self.client.disconnect()