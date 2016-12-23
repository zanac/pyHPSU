#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import serial, sys, getopt, time, csv

class CanELM327(object):
    def __init__(self):
        pass
    
    def initInterface(self, portstr=None, baudrate=38400, init=False):
        try:
            self.ser = serial.Serial(portstr, baudrate, timeout=1)
            self.ser.close()
            self.ser.open()
        except serial.SerialException:
            print "Error opening serial %s" % portstr
            sys.exit(9)

        if init:
            rc = self.sendCommand("ATE0")
            if rc != "OK":
                print "Error sending ATE0 (rc:%s)" % rc
                sys.exit(9)
            
            rc = self.sendCommand("AT PP 2F SV 19")
            rc = "OK"
            if rc != "OK":
                print "Error sending AT PP 2F SV 19 (rc:%s)" % rc
                sys.exit(9)
            
            rc = self.sendCommand("AT PP 2F ON")
            rc = "OK"
            if rc != "OK":
                print "Error sending AT PP 2F ON (rc:%s)" % rc
                sys.exit(9)
            
            rc = self.sendCommand("AT D")
            rc = "OK"
            if rc != "OK":
                print "Error sending AT D (rc:%s)" % rc
                sys.exit(9)
            
            rc = self.sendCommand("AT SP C")
            if rc != "OK":
                print "Error sending AT SP C (rc:%s)" % rc
                sys.exit(9)

    def sendCommand(self, cmd):
        self.ser.write("%s\r\n" % cmd)
        time.sleep(50.0 / 1000.0)
        ser_read = self.ser.read(size=100)
        rc = ser_read[:-3]
        return rc
    
    def sendCommandWithID(self, cmd):
        rc = self.sendCommand("ATSH"+cmd["receiver_id"])
        if rc != "OK":
            return "Error setting ID %s (rc:%s)" % (cmd["receiver_id"], rc)
        
        rc = self.sendCommand(cmd["command"])
        #rc = "32 10 FA 01 D6 01 0C"
        #rc = "32 10 02 01 01 00 00"
        if rc[0:1] != cmd[0:1]:
            return "Error sending cmd %s (rc:%s)" % (cmd["command"], rc)
        
        return rc
    
    def getInterface(self):
        return self.sendCommand("ATI")
