#!/usr/bin/env python3
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
        try:
            self.ser.close()
        except:
            pass
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

    def sendCommand(self, cmd, setValue=None, um=None):
        if setValue:
            cmd = cmd[:1] + '2' + cmd[2:]
            if cmd[6:8] != "FA":
                cmd = cmd[:3]+"00 FA"+cmd[2:8]
            cmd = cmd[:14]
            if um == "d":
                setValue = int(setValue)
                if setValue < 0:
                    setValue = 0x10000+setValue
                cmd = cmd+" %02X %02X" % (setValue >> 8, setValue & 0xff)
            if um == "i":
                setValue = int(setValue)
                cmd = cmd+" %02X 00" % (setValue)    
    
        self.ser.write(bytes(str("%s\r\n" % cmd).encode('utf-8')))
        time.sleep(50.0 / 1000.0)
        if setValue:
            return "OK"

        ser_read = self.ser.read(size=100)
        rc = ser_read.decode('utf-8')[:-3]
        rc = rc.replace("\r", "").replace("\n", "").strip()
        return rc
    
    def sendCommandWithID(self, cmd, setValue=None, priority=1):
        if setValue:
            rc = self.sendCommand("ATSH680")
        else:
            rc = self.sendCommand("ATSH"+cmd["receiver_id"])
        if rc != "OK":
            #self.eprint("Error setting ID %s (rc:%s)" % (cmd["receiver_id"], rc))
            self.resetInterface()
            self.hpsu.printd('warning', "Error setting ID %s (rc:%s)" % (cmd["receiver_id"], rc))
            return "KO"
        
        rc = self.sendCommand(cmd["command"], setValue, cmd["um"])
        if setValue:
            return rc

        if rc[0:1] != cmd["command"][0:1]:
            #self.eprint("Error sending cmd %s (rc:%s)" % (cmd["command"], rc))
            self.resetInterface()
            self.hpsu.printd('warning', 'sending cmd %s (rc:%s)' % (cmd["command"], rc))
            return "KO"
        
        return rc
    
    def getInterface(self):
        return self.sendCommand("ATI")
