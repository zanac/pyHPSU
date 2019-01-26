#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [OPENHAB]
# HOST = hostname_or_ip
# PORT = 8080
# ITEMPREFIX = Rotex_

import socket
import configparser
import sys
import os
import requests


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

        # openhab hostname or IP
        if self.config.has_option('OPENHAB', 'HOST'):
            self.openhabhost = self.config['OPENHAB']['HOST']
        else:
            self.openhabhost = 'localhost'

        # openhab port
        if self.config.has_option('OPENHAB', 'PORT'):
            self.openhabport = int(self.config['OPENHAB']['PORT'])
        else:
            self.openhabport = 8080

        # openhab item name
        if self.config.has_option('OPENHAB', 'ITEMPREFIX'):
            self.openhabitemprefix = self.config['OPENHAB']['ITEMPREFIX']
        else:
            self.openhabitemprefix = 'Rotex_'

    def rest_send(self, name, data):
        url = "http://" + str(self.openhabhost) + ":" + str(self.openhabport) + "/rest/items/" + self.openhabitemprefix + name + "/state"
        headers = "Content-Type: text/plain"
        try:
            r = requests.put(url, data=data, headers=headers)
        except (r.ConnectionError, r.HTTPError) as e:
            rc = "ko"
            self.hpsu.printd("exception", "Error " + str(e.code) + ": " + str(e.reason))

    def pushValues(self, vars=None):
        for r in vars:
            self.rest_send(self, r['name'], r['resp']) 

    #if __name__ == '__main__':
    #    app = openhab()

    #    app.exec_()
