#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import sys
import socket
import time

SocketPort = 7060

class CanTCP(object):
    sock = None
    hpsu = None
    
    def __init__(self, hpsu=None):
        self.hpsu = hpsu
    
    def initInterface(self):
        pass        
    
    def sendCommandWithID(self, cmd, setValue=None):    
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3.5)
        self.sock.connect(('127.0.0.1', SocketPort))
        
        if setValue:
            dataSEND = "%s:%s\r\n" % (cmd["name"], setValue)
        else:
            dataSEND = "%s\r\n" % cmd["name"]

        try:
            self.sock.send(dataSEND.encode())
        except socket.timeout:
            return "KO"
        
        time.sleep(0.1)
                
        try:
            dataRECV = self.sock.recv(512)
        except socket.timeout:
            return "KO"

        time.sleep(0.1)
        self.sock.close()
        return dataRECV.decode('UTF-8')
