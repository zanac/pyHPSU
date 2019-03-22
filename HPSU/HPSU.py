#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import platform
import sys
from HPSU.canelm327 import CanELM327
from HPSU.canemu import CanEMU
from HPSU.canpi import CanPI
from HPSU.cantcp import CanTCP
import platform
import datetime
import locale
import sys
import csv
import json
import os.path
import time

class HPSU(object):
    commands = []
    listCommands = []
    UM_DEGREE = "deg"
    UM_BOOLEAN = "bool"
    UM_PERCENT = "percent"
    UM_INT = "int"
    UM_BAR = "bar"
    UM_HOUR = "hour"
    driver = None
    
    pathCOMMANDS = "/etc/pyHPSU"    

    def __init__(self, logger=None, driver=None, port=None, cmd=None, lg_code=None):
        self.can = None            
        self.commands = []              # data for all commands requested
        self.listCommands = []          # all usable commands from csv
        self.logger = logger
        self.command_dict={}
        self.backup_commands=[]
        
        listCmd = [r.split(":")[0] for r in cmd]

        if not self.listCommands: #if we don't get a dict with commands

            # get language, if non given, take it from the system
            LANG_CODE = lg_code.upper()[0:2] if lg_code else locale.getdefaultlocale()[0].split('_')[0].upper()
            hpsuDict = {}
            
            # read the translation file. if it doesn't exist, take the english one
            commands_hpsu = '%s/commands_hpsu_%s.csv' % (self.pathCOMMANDS, LANG_CODE)
            if not os.path.isfile(commands_hpsu):
                commands_hpsu = '%s/commands_hpsu_%s.csv' % (self.pathCOMMANDS, "EN")
            # check, if commands are json or csv
            # read all known commands
            with open(commands_hpsu, 'rU',encoding='utf-8') as csvfile:
                pyHPSUCSV = csv.reader(csvfile, delimiter=';', quotechar='"')
                next(pyHPSUCSV, None) # skip the header
                for row in pyHPSUCSV:
                    name = row[0]
                    label = row[1]
                    desc = row[2]
                    hpsuDict.update({name:{"label":label, "desc":desc}})

            # read all known commands

            with open('%s/commands_hpsu.json' % self.pathCOMMANDS, 'rU',encoding='utf-8') as jsonfile:
                self.all_commands = json.load(jsonfile)
                self.command_dict=self.all_commands["commands"]
                for single_command in self.command_dict:
                    if single_command in hpsuDict:
                        self.command_dict[single_command].update({ "label" : hpsuDict[single_command]["label"], "desc" : hpsuDict[single_command]["desc"]})
                    if (single_command in listCmd) or (len(listCmd) == 0):                        
                        self.commands.append(self.command_dict[single_command])
                    if (self.command_dict[single_command]["writable"]=="true"):
                        self.backup_commands.append(self.command_dict[single_command]["name"])

        self.driver = driver
        if self.driver == "ELM327":
            self.can = CanELM327(self)
        elif self.driver == "EMU":
            self.can = CanEMU(self)        
        elif self.driver == "PYCAN":
            self.can = CanPI(self)
        elif self.driver == "HPSUD":
            self.can = CanTCP(self)
        else:
            print("Error selecting driver %s" % self.driver)
            sys.exit(9)

        self.initInterface(port)

    def printd(self, level, msg):        
        if self.logger:
            if level == 'warning':
                self.logger.warning(msg)
            elif level == 'error':
                self.logger.error(msg)
            elif level == 'info':
                self.logger.info(msg)
            elif level == 'exception':
                self.logger.exception(msg)
        else:
            print("%s - %s" % (level, msg))
    
    def sendCommandWithParse(self, cmd, setValue=None, priority=1):
        response = None
        verbose = "1"        
        i = 1
        
        while i <= 3:
            rc = self.sendCommand(cmd, setValue=setValue, priority=priority)
            if rc != "KO":
                i = 4
                if not setValue:
                    response = self.parseCommand(cmd=cmd, response=rc, verbose=verbose)["resp"]
                else:
                    response = ""
            else:
                i += 1
                time.sleep(2.0)
        return response
    
    def getParameterValue(self, parameter, priority=1):
        response = None
        cmd = None
        for c in self.commands:
            if c["name"] == parameter:
                cmd = c
        if cmd:
            response = self.sendCommandWithParse(cmd=cmd, priority=priority)
        
        return response 
    
    def setParameterValue(self, parameter, setValue, priority=1):
        response = None
        cmd = None
        for c in self.commands:
            if c["name"] == parameter:
                cmd = c
        
        if cmd:
            response = self.sendCommandWithParse(cmd=cmd, setValue=setValue, priority=priority)
        
        return response 
                

    def initInterface(self, portstr=None, baudrate=38400, init=False):
        if self.driver == "ELM327":
            self.can.initInterface(portstr=portstr, baudrate=baudrate,init=True)
        elif self.driver == "HPSUD":
            self.can.initInterface()
    
    # funktion to set/read a value
    def sendCommand(self, cmd, setValue=None, priority=1):
        rc = self.can.sendCommandWithID(cmd=cmd, setValue=setValue, priority=priority)

        if rc not in ["KO", "OK"]:
            try:
                hexValues = [int(r, 16) for r in rc.split(" ")]
            except ValueError:
                return "KO"
        return rc
        
    def timestamp(self):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return (datetime.datetime.now() - epoch).total_seconds() * 1000.0
        
    def toSigned(self, n, cmd):
        if cmd["unit"] == "deg":
            n = n & 0xffff
            return (n ^ 0x8000) - 0x8000
        else:
            return n
        
        
    def parseCommand(self, cmd, response, verbose):
        hexValues = [int(r, 16) for r in response.split(" ")]
        hexArray = response.split(" ")
        

        if cmd["type"] == "int":
            if hexValues[2] == 0xfa:
                resp = int(self.toSigned(hexValues[5], cmd) // float(cmd["divisor"]))
            else:
                resp = int(self.toSigned(hexValues[3], cmd) // float(cmd["divisor"]))
    
        elif cmd["type"] == "longint":
            if hexValues[2] == 0xfa:
                resp = int(self.toSigned(hexValues[5]*0x100+hexValues[6], cmd) // float(cmd["divisor"]))
            else:
                resp = int(self.toSigned(hexValues[3]*0x100+hexValues[4], cmd) // float(cmd["divisor"]))

        elif cmd["type"] == "float":
            if hexValues[2] == 0xfa:
                resp = self.toSigned(hexValues[5]*0x100+hexValues[6], cmd) / float(cmd["divisor"])
            else:
                resp = self.toSigned(hexValues[3]*0x100+hexValues[4], cmd) / float(cmd["divisor"])
        elif cmd["type"] == "value":
            if hexValues[2] == 0xfa:
                resp = int(str(hexArray[5]) + str(hexArray[6]),16) // int(cmd["divisor"])
            else:
                resp = int(str(hexArray[3]) + str(hexArray[4]),16) // int(cmd["divisor"])

        if verbose == "2":
            timestamp = datetime.datetime.now().isoformat()
        else:
            if sys.version_info >= (3, 0):
                timestamp = datetime.datetime.now().timestamp()
            else:
                timestamp = self.timestamp()

        return {"resp":resp, "timestamp":timestamp}

    
    def umConversion(self, cmd, response, verbose):
        # convert into different units
        resp = response["resp"]

        if cmd["unit"] == HPSU.UM_DEGREE:
            resp = locale.format("%.2f", round(response["resp"], 2))
            if verbose == "2":
                resp = "%s c" % resp
        elif cmd["unit"] == HPSU.UM_BOOLEAN:
            resp = int(response["resp"])
            if verbose == "2":
                resp = "ON" if resp == 1 else "OFF"
        elif cmd["unit"] == HPSU.UM_PERCENT:
            resp = int(response["resp"])
            if verbose == "2":
                resp = "%s%%" % int(response["resp"])
        elif cmd["unit"] == HPSU.UM_INT:
            resp = str(response["resp"])
        else:
            resp = str(response["resp"])
        #if cmd["value_code"]:
        #    resp=cmd["value_code"][resp]
        return resp
