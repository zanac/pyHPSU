#!/usr/bin/env python
# -*- coding: utf-8 -*-
import platform
import sys
"""if platform.system() == "Windows":
    sys.path.append('C:/Sec/apps/Apache24/htdocs/domon')
else:
    sys.path.append('/home/domon/domon/')
    sys.path.append('/home/domon/domon/web/')
    sys.path.append('/home/domon/domon/web/waterpump/')"""
from .canelm327 import CanELM327
from .canemu import CanEMU
from .canpi import CanPI
from .cantcp import CanTCP
import platform
import datetime
import locale
import sys
import csv
import os.path
import time

class HPSU(object):
    commands = []
    listCommands = []
    UM_DEGREE = "d"
    UM_BOOLEAN = "b"
    UM_PERCENT = "perc"
    driver = None
    
    pathCOMMANDS = "/etc/pyHPSU"    

    def __init__(self, driver=None, port=None, cmd=None, lg_code=None):
        self.can = None            
        self.commands = []
        self.listCommands = []
        
        if platform.system() == "Windows":
            self.pathCOMMANDS = "C:/Sec/apps/Apache24/htdocs/domon/waterpump%s" % self.pathCOMMANDS        
        
        LANG_CODE = lg_code if lg_code else locale.getdefaultlocale()[0].split('_')[0].upper()
        hpsuDict = {}
        
        commands_hpsu = '%s/commands_hpsu_%s.csv' % (self.pathCOMMANDS, LANG_CODE)
        if not os.path.isfile(commands_hpsu):
            commands_hpsu = '%s/commands_hpsu_%s.csv' % (self.pathCOMMANDS, "EN")

        with open(commands_hpsu, 'rU') as csvfile:
            pyHPSUCSV = csv.reader(csvfile, delimiter=';', quotechar='"')
            next(pyHPSUCSV, None) # skip the header
            for row in pyHPSUCSV:
                name = row[0]
                label = row[1]
                desc = row[2]
                hpsuDict.update({name:{"label":label, "desc":desc}})
            
        with open('%s/commands_hpsu.csv' % self.pathCOMMANDS, 'rU') as csvfile:
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
    
    def sendCommandWithParse(self, cmd):
        response = None
        verbose = "1"        
        i = 1
        
        while i <= 3:
            rc = self.sendCommand(cmd)
            if rc != "KO":
                i = 4
                response = self.parseCommand(cmd=cmd, response=rc, verbose=verbose)["resp"]
            else:
                i += 1
                time.sleep(2.0)
        return response

    def getParameterValue(self, parameter):
        response = None
        cmd = None
        for c in self.commands:
            if c["name"] == parameter:
                cmd = c
        
        if cmd:
            response = self.sendCommandWithParse(cmd)
        
        return response
                

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
        
    def toSigned(self, n, cmd):
        if cmd["um"] == "d":
            n = n & 0xffff
            return (n ^ 0x8000) - 0x8000
        else:
            return n
        
        
    def parseCommand(self, cmd, response, verbose):
        hexValues = [int(r, 16) for r in response.split(" ")]
        
        if hexValues[2] == 0xfa:
            resp = float(self.toSigned(hexValues[5]*0x100+hexValues[6], cmd)) / int(cmd["div"])
        else:
            resp = float(self.toSigned(hexValues[3]*0x100+hexValues[4], cmd)) / int(cmd["div"])
        
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
