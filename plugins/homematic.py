#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [HOMEMATIC]
# METHOD = xmlapi
# HOST = HOSTNAME_OR_IP_CCU
# PORT = 80

import socket
import configparser
import sys
import os
import urllib.request


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

        # homematic's hostname or IP
        if self.config.has_option('HOMEMATIC', 'HOST'):
            self.homematichost = self.config['HOMEMATIC']['HOST']
        else:
            self.fhost = 'localhost'

        # homematic's port
        if self.config.has_option('HOMEMATIC', 'PORT'):
            self.homematicport = int(self.config['HOMEMATIC']['PORT'])
        else:
            self.homematicport = 80

        # method to put the data 
        if self.config.has_option('HOMEMATIC','METHOD'):
            self.method=self.config['HOMEMATIC']['METHOD']
        else:
            self.method="xmlapi"

    def xmlapi_send(self, url):
        self.url=url
        req=urllib.request.Request(self.url)
        try:
            urllib.request.urlopen(req)
        except urllib.error.URLError as e:
            rc = "ko"
            self.hpsu.printd("exception", "Error " + str(e.code) + ": " + str(e.reason))

    def pushValues(self, vars=None):
        if self.method == "xmlapi":
            for r in vars:
                self.ISE_ID=self.config['HOMEMATIC'][r['name']]
                self.url_string="http://" + str(self.homematichost) + ":" + str(self.homematicport) + "/config/xmlapi/statechange.cgi?ise_id=" + self.ISE_ID + "&new_value=" + str(r['resp'])
                self.xmlapi_send(self.url_string) 

    #if __name__ == '__main__':
    #    app = homematic()

    #    app.exec_()
