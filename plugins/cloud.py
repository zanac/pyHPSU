#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import requests
import sys


class Cloud():
    hpsu = None
    
    def get_with_default(self, config, section, name, default):
        if "config" not in config.sections():
            return default
        
        if config.has_option(section,name):
            return config.get(section,name)
        else:
            return default
        
    def __init__(self, plugin=None, hpsu=None, logger=None):
        self.plugin = plugin
        self.hpsu = hpsu
        self.logger = logger

        #Legge file emoncms.ini
        config = configparser.ConfigParser()
        iniFile = '%s/%s.ini' % (self.hpsu.pathCOMMANDS, plugin)
        config.read(iniFile)
        self.apikey = self.get_with_default(config=config, section="config", name="apikey", default=None)
                
        self.listNodes = {}
        self.listCmd = []
        options = config.options("node")
        for option in options:
            try:
                self.listNodes[option] = config.get("node", option).split(',')
                self.listCmd.extend(self.listNodes[option])
                
                for c in self.listNodes[option]:
                    InCommand = True
                    for j in self.hpsu.commands:
                        if c == j["name"]:
                            InCommand = False
                    if InCommand:
                        self.hpsu.printd("warning", "command %s defined in emoncms but not in extraction" % c)

            except:
                self.listNodes[option] = None
        
        for r in self.hpsu.commands:
            if r["name"] not in self.listCmd:
                self.hpsu.printd("warning", "command %s defined in extraction but not in emoncms" % r["name"])

    def pushValues(self, vars):
        if self.plugin == "EMONCMS":
            timestamp = None
            
            for node in self.listNodes:
                nodeName = node[5:]
                
                varsDict = {}
                for r in vars:
                    if not timestamp:
                        timestamp = r["timestamp"]
                                        
                    for r2 in self.listNodes[node]:
                        if r2 == r["name"]:
                            varsDict.update({r["name"]:r["resp"]})
                if len(varsDict) > 0:
                    varsTxt = str(varsDict).replace(" ", "")
                    _url = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=%s" % (self.apikey, timestamp, varsTxt, nodeName)
                    _urlNoApi = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=%s" % ('xxx', timestamp, varsTxt, nodeName)
                    
                    try:
                        r = requests.get(_url, timeout=7)
                        rc = r.text
                    except (requests.exceptions.Timeout, e):
                        rc = "ko"
                        self.hpsu.printd("exception", "Connection timeout during get %s" % _urlNoApi)
                    except Exception:
                        rc = "ko"
                        self.hpsu.printd("exception", "Exception on get %s" % _urlNoApi)
                    
                    
                
            return True

        if self.plugin == "DOMON":
            print ("tbd")

