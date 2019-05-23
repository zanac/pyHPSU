#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import requests
import sys
import os

# config inf conf_file (defaults):
# [EMONCMS]
# URL = https://emoncms.org
# node_1 = t_hs, t_hs_setpoint
# node_2 = qoh....
# ......
# ......


class export():
    hpsu = None
    
    def get_with_default(self, config, section, name, default):
        if "config" not in config.sections():
            return default
        
        if config.has_option(section,name):
            return config.get(section,name)
        else:
            return default
        
    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.hpsu = hpsu
        self.logger = logger
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            self.config.read(self.config_file)
        else:
            sys.exit(9)

        # URL to emoncms server
        if self.config.has_option('EMONCMS', 'URL'):
            self.emonurl = self.config['EMONCMS']['URL']
        else:
            self.emonurl = 'https://emoncms.org'

        # API-Key
        if self.config.has_option('EMONCMS', 'APIKEY'):
            self.emonkey = self.config['EMONCMS']['APIKEY']
        else:
            self.emonkey = 'xxxxxxxxxx'    

        self.listNodes = {}
        self.listCmd = []
        options = self.config.options("EMONCMS")
        for option in options:
            if option.startswith("node_"):
                try:
                    self.listNodes[option] = self.config.get("EMONCMS", option).split(',')
                    self.listCmd.extend(self.listNodes[option])
                    
                    for c in self.listNodes[option]:
                        InCommand = True
                        for j in self.hpsu.commands:
                            if c == j["name"]:
                                InCommand = False
                        if InCommand:
                            self.hpsu.printd("warning", "command %s defined in emoncms but not as commandline option" % c)

                except:
                    self.listNodes[option] = None
        
        for r in self.hpsu.commands:
            if r["name"] not in self.listCmd:
                self.hpsu.printd("warning", "command %s defined as commandline option but not in emoncms" % r["name"])

    def pushValues(self, vars):
        #if self.plugin == "EMONCMS":
        #    timestamp = None
            
        #    for node in self.listNodes:
#		Commented out...why are the first 5 characters are stripped?
#                nodeName = node[5:]
        timestamp = None
        for node in self.listNodes:
            nodeName = node                
            varsDict = {}
            for r in vars:
                if not timestamp:
                    timestamp = r["timestamp"]
                                        
                for r2 in self.listNodes[node]:
                    if r2 == r["name"]:
                        varsDict.update({r["name"]:r["resp"]})
            if len(varsDict) > 0:
                varsTxt = str(varsDict).replace(" ", "")
#               _url = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=%s" % (self.apikey, timestamp, varsTxt, nodeName)
#                _urlNoApi = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=%s" % ('xxx', timestamp, varsTxt, nodeName)
                _url = "%s/input/post?apikey=%s&time:%s&json=%s&node=%s" % (self.emonurl, self.emonkey, timestamp, varsTxt, nodeName)
                _urlNoApi = "%s/input/post?apikey=%s&time:%s&json=%s&node=%s" % (self.emonurl, 'xxx', timestamp, varsTxt, nodeName)
                                 
                try:
                    r = requests.get(_url, timeout=7)
                    rc = r.text
                except (requests.exceptions.Timeout):
                    rc = "ko"
                    self.hpsu.printd("exception", "Connection timeout during get %s" % _urlNoApi)
                except (requests.exceptions.ConnectionError):
                    self.hpsu.printd("exception", "Failed to establish a new connection to %s" % _urlNoApi)
                except Exception:
                    rc = "ko"
                    self.hpsu.printd("exception", "Exception on get %s" % _urlNoApi)
                    
        return True