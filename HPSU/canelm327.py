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
            self.hpsu.logger.error("Error opening serial %s" % portstr)
            sys.exit(9)

        if init:
            rc = self.sendCommand("ATE0")
                        
            rc = self.sendCommand("AT PP 2F ON")
            """ if rc != "OK":
                self.hpsu.logger.error("Error sending AT PP 2F ON (rc:%s)" % rc)
                sys.exit(9) """
            count_1=0
            while rc != "OK":
                if count_1==15:
                    self.hpsu.logger.error("can adapter not responding: (rc:%s)" % rc)
                    sys.exit(9)
                else:
                    self.hpsu.logger.error("Error sending AT PP 2F ON (rc:%s)" % rc)
                    count_1+=1
                    time.sleep(1)

            """rc = self.sendCommand("AT D")
            if rc != "OK":
                self.hpsu.logger.error("Error sending AT D (rc:%s)" % rc)
                sys.exit(9)"""
            
            rc = self.sendCommand("AT SP C")
            count_2=0
            while rc != "OK":
                if count_2==15:
                    self.hpsu.logger.error("can adapter not responding: (rc:%s)" % rc)
                    sys.exit(9)
                else:  
                    self.hpsu.logger.error("Error sending AT SP C (rc:%s)" % rc)
                    count_2+=1
                    time.sleep(1)

    def sendCommand(self, cmd, setValue=None, type=None):
        command = ""
        
        if setValue and type:
            command = cmd[:1] + '2' + cmd[2:]
            if command[6:8] != "FA":
                command = command[:3]+"00 FA"+command[2:8]
            command = command[:14]

            if type == "int":
                setValue = int(setValue)
                command = command+" %02X 00" % (setValue)
            if type == "longint":
                setValue = int(setValue)
                command = command+" 00 %02X" % (setValue)
            if type == "float":
                setValue = int(setValue)
                if setValue < 0:
                    setValue = 0x10000+setValue
                command = command+" %02X %02X" % (setValue >> 8, setValue & 0xff)
            if type == "value":
                setValue = int(setValue)
                command = command+" 00 %02X" % (setValue)

            #self.hpsu.logger.info("cmd: %s cmdMod: %s" % (cmd, command))
            cmd = command

        self.ser.write(bytes(str("%s\r\n" % cmd).encode('utf-8')))
        time.sleep(50.0 / 1000.0)
        if setValue and type:
            return "OK"

        ser_read = self.ser.read(size=100)
        rc = ser_read.decode('utf-8')[:-3]
        rc = rc.replace("\r", "").replace("\n", "").strip()
        return rc
    
    def sendCommandWithID(self, cmd, setValue=None, priority=1):
        if setValue:
            rc = self.sendCommand("ATSH680")
        else:
            rc = self.sendCommand("ATSH"+cmd["id"])
        if rc != "OK":
            self.resetInterface()
            self.hpsu.logger.warning("Error setting ID %s (rc:%s)" % (cmd["id"], rc))
            return "KO"
        
        rc = self.sendCommand(cmd["command"], setValue, cmd["type"])
        if setValue:
            return rc

        if rc[0:1] != cmd["command"][0:1]:
            self.resetInterface()
            self.hpsu.logger.warning('sending cmd %s (rc:%s)' % (cmd["command"], rc))
            return "KO"
        
        return rc
    
    def getInterface(self):
        return self.sendCommand("ATI")
