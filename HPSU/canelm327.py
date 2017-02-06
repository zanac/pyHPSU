#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import serial
import sys
import time

class CanELM327(object):
    portstr = None
    hpsu = None
    def __init__(self, hpsu=None):
        self.hpsu = hpsu
    
    def resetInterface(self):
        self.ser.flushInput()  #flush input buffer, discarding all its contents
        self.ser.flushOutput() #flush output buffer, aborting current output and discard all that is in buffer
        self.initInterface(self.portstr, 38400, True)
    
    def initInterface(self, portstr=None, baudrate=38400, init=False):
        self.portstr = portstr
        try:
            self.ser = serial.Serial(portstr, baudrate, timeout=1)
            self.ser.close()
            self.ser.open()
            self.ser.flushInput()  #flush input buffer, discarding all its contents
            self.ser.flushOutput() #flush output buffer, aborting current output and discard all that is in buffer
        except serial.SerialException:
            self.hpsu.printd("error", "Error opening serial %s" % portstr)
            sys.exit(9)

        if init:
            rc = self.sendCommand("ATE0")
                        
            rc = self.sendCommand("AT PP 2F ON")
            if rc != "OK":
                self.hpsu.printd("error", "Error sending AT PP 2F ON (rc:%s)" % rc)
                sys.exit(9)
            
            """rc = self.sendCommand("AT D")
            if rc != "OK":
                print "Error sending AT D (rc:%s)" % rc
                sys.exit(9)"""
            
            rc = self.sendCommand("AT SP C")
            if rc != "OK":
                self.hpsu.printd("error", "Error sending AT SP C (rc:%s)" % rc)
                sys.exit(9)

    def sendCommand(self, cmd):
        self.ser.write("%s\r\n" % cmd)
        time.sleep(50.0 / 1000.0)
        ser_read = self.ser.read(size=100)
        rc = ser_read[:-3]
        rc = rc.replace("\r", "").replace("\n", "").strip()
        return rc
    
    def sendCommandWithID(self, cmd):
        rc = self.sendCommand("ATSH"+cmd["receiver_id"])
        if rc != "OK":
            #self.eprint("Error setting ID %s (rc:%s)" % (cmd["receiver_id"], rc))
            self.resetInterface()
            self.hpsu.printd('warning', "Error setting ID %s (rc:%s)" % (cmd["receiver_id"], rc))
            return "KO"
        
        rc = self.sendCommand(cmd["command"])
        if rc[0:1] != cmd["command"][0:1]:
            #self.eprint("Error sending cmd %s (rc:%s)" % (cmd["command"], rc))
            self.resetInterface()
            self.hpsu.printd('warning', 'sending cmd %s (rc:%s)' % (cmd["command"], rc))
            return "KO"
        
        return rc
    
    def getInterface(self):
        return self.sendCommand("ATI")
