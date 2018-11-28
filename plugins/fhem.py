#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [FHEM]
# METHOD = telnet
# HOST = localhost
# PORT = 7072
# DEVICE = HPSU

import socket
import configparser
import requests
import sys
import os


class fhem():
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

        # fhem's telnet hostname
        if self.config.has_option('FHEM', 'HOST'):
            self.fhemhost = self.config['FHEM']['HOST']
        else:
            self.fhemhost = 'localhost'

        # fhem's telnet port
        if self.config.has_option('FHEM', 'PORT'):
            self.fhemport = int(self.config['FHEM']['PORT'])
        else:
            self.fhemport = 7072

        # fhem's device name
        if self.config.has_option('FHEM', 'DEVICE'):
            self.fhemdevice = self.config['FHEM']['DEVICE']
        else:
            self.fhemdevice = 'HPSU'

        # method to put the data 
        if self.config.has_option('FHEM','METHOD'):
            self.method=self.config['FHEM']['METHOD']
        else:
            self.method="telnet"

    def netcat(self, hostname, fhemport, content):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, fhemport))
        s.sendall((content).encode())
        s.shutdown(socket.SHUT_WR)
        s.close()

    def pushValues(self, vars=None):
        if self.method == "telnet":
            for r in vars:
                # empty netcat string
                s = ""
                u = ""
                u += ("%s %s" % (r["name"], r["resp"]))
                s += 'setreading ' + self.fhemdevice + ' pyHPSU.' + u + '\n'
                s += "quit"
                self.netcat(self.fhemhost, self.fhemport, s)

    if __name__ == '__main__':
        app = fhem()

        app.exec_()
