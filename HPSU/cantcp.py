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
    
    def sendCommandWithID(self, cmd):    
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', SocketPort))
        
        dataSEND = "%s\r\n" % cmd["name"]
        self.sock.send(dataSEND.encode())
        time.sleep(0.1)
                
        dataRECV = self.sock.recv(512)
        time.sleep(0.1)
        self.sock.close()
        return dataRECV.decode('UTF-8')
