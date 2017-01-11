#!/usr/bin/env python
# -*- coding: utf-8 -*-
from canelm327 import CanELM327
from canemu import CanEMU
from canpi import CanPI
from cantcp import CanTCP
import datetime
import locale
import sys
import csv
import os.path

class HPSU(object):
    commands = []
    listCommands = []
    UM_DEGREE = "d"
    UM_BOOLEAN = "b"
    UM_PERCENT = "perc"
    driver = None

    def __init__(self, driver=None, port=None, cmd=None):
        self.can = None            
        self.commands = []
        self.listCommands = []
        
        LANG_CODE = locale.getdefaultlocale()[0].split('_')[0].upper()
        hpsuDict = {}
        
        commands_hpsu = 'commands_hpsu_%s.csv' % LANG_CODE
        if not os.path.isfile(commands_hpsu):
            commands_hpsu = 'commands_hpsu_%s.csv' % "EN"

        with open(commands_hpsu, 'rU') as csvfile:
            pyHPSUCSV = csv.reader(csvfile, delimiter=';', quotechar='"')
            next(pyHPSUCSV, None) # skip the header
            for row in pyHPSUCSV:
                name = row[0]
                label = row[1]
                desc = row[2]
                hpsuDict.update({name:{"label":label, "desc":desc}})
            
        with open('commands_hpsu.csv', 'rU') as csvfile:
            pyHPSUCSV = csv.reader(csvfile, delimiter=';', quotechar='"')
            next(pyHPSUCSV, None) # skip the header

            for row in pyHPSUCSV:
                name = row[0]
                command = row[1]
                receiver_id = row[2]
                um = row[3]
                div = row[4]
                label = hpsuDict[name]["label"]
                desc = hpsuDict[name]["desc"]
                
                c = {"name":name,
                     "desc":desc,
                     "label":label,
                     "command":command,
                     "receiver_id":receiver_id,
                     "um":um,
                     "div":div}
                
                self.listCommands.append(c)
                if (name in cmd) or (len(cmd) == 0):
                    self.commands.append(c)
        
        self.driver = driver
        if self.driver == "ELM327":
            self.can = CanELM327()
        elif self.driver == "EMU":
            self.can = CanEMU()        
        elif self.driver == "PYCAN":
            self.can = CanPI()
        elif self.driver == "HPSUD":
            self.can = CanTCP()
        else:
            print("Error selecting driver %s" % self.driver)
            sys.exit(9)

        self.initInterface(port)


    def initInterface(self, portstr=None, baudrate=38400, init=False):
        if self.driver == "ELM327":
            self.can.initInterface(portstr=portstr, baudrate=baudrate,init=True)
        elif self.driver == "HPSUD":
            self.can.initInterface()
    
    def sendCommand(self, cmd):
        return self.can.sendCommandWithID(cmd)
        
    def timestamp(self):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return (datetime.datetime.now() - epoch).total_seconds() * 1000.0
        
    def toSigned(self, n):
        n = n & 0xffff
        return (n ^ 0x8000) - 0x8000
        
        
    def parseCommand(self, cmd, response, verbose):
        hexValues = [int(r, 16) for r in response.split(" ")]
        
        if hexValues[2] == 0xfa:
            resp = float(self.toSigned(hexValues[5]*0x100+hexValues[6])) / int(cmd["div"])
        else:
            resp = float(self.toSigned(hexValues[3]*0x100+hexValues[4])) / int(cmd["div"])
        
        if verbose == "2":
            timestamp = datetime.datetime.now().isoformat()
        else:
            if sys.version_info >= (3, 0):
                timestamp = datetime.datetime.now().timestamp()
            else:
                timestamp = self.timestamp()
        return {"resp":resp, "timestamp":timestamp}
    
    def umConversion(self, cmd, response, verbose):
        resp = response["resp"]

        if cmd["um"] == HPSU.UM_DEGREE:
            resp = locale.format("%.2f", round(response["resp"], 2))
            if verbose == "2":
                resp = "%s c" % resp
        elif cmd["um"] == HPSU.UM_BOOLEAN:
            resp = int(response["resp"])
            if verbose == "2":
                resp = "ON" if resp == 1 else "OFF"
        elif cmd["um"] == HPSU.UM_PERCENT:
            if verbose == "2":
                resp = "%s%%" % int(response["resp"])
        else:
            resp = str(response["resp"])
        
        return resp
