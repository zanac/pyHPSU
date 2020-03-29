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
            sys.exit(9)

        # MQTT hostname or IP
        if self.config.has_option('MQTT', 'BROKER'):
            self.brokerhost = self.config['MQTT']['BROKER']
        else:
            self.brokerhost = 'localhost'

        # MQTT broker port
        if self.config.has_option('MQTT', 'PORT'):
            self.brokerport = int(self.config['MQTT']['PORT'])
        else:
            self.brokerport = 1883

        # MQTT client name
        if self.config.has_option('MQTT', 'CLIENTNAME'):
            self.clientname = self.config['MQTT']['CLIENTNAME']
        else:
            self.clientname = 'rotex'
        # MQTT Username
        if self.config.has_option('MQTT', 'USERNAME'):
            self.username = self.config['MQTT']['USERNAME']
        else:
            self.username = None
            print("Username not set!!!!!")

        #MQTT Password
        if self.config.has_option('MQTT', "PASSWORD"):
            self.password = self.config['MQTT']['PASSWORD']
        else:
            self.password="None"

        #MQTT Prefix
        if self.config.has_option('MQTT', "PREFIX"):
            self.prefix = self.config['MQTT']['PREFIX']
        else:
            self.prefix = ""

        #MQTT QOS
        if self.config.has_option('MQTT', "QOS"):
            self.qos = self.config['MQTT']['QOS']
        else:
            self.qos = "0"

        self.client=mqtt.Client(self.clientname)
        #self.client.on_publish = self.on_publish()
        if self.username:
           self.client.username_pw_set(self.username, password=self.password)
        self.client.enable_logger()

    
        
    #def on_publish(self,client,userdata,mid):
    #   print("data published, mid: " + str(mid) + "\n")
    #    pass


    def pushValues(self, vars=None):
        self.client.connect(self.brokerhost, port=self.brokerport)
        #self.msgs=[]
        for r in vars:
            msgs=[]
            if self.prefix:
                ret=self.client.publish(self.prefix + "/" + r['name'],payload=r['resp'], qos=int(self.qos))
                topic=self.prefix + "/" + r['name']
            else:
                ret=self.client.publish(r['name'],payload=r['resp'])
                topic=r['name']
            msg={'topic':topic,'payload':r['resp'], 'qos':self.qos, 'retain':False}
        self.client.disconnect()

       



   
