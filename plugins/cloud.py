#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser, requests, sys

class Cloud():
    pathCOMMANDS = ""
    
    def get_with_default(self, config, section, name, default):
        if "config" not in config.sections():
            return default
        
        if config.has_option(section,name):
            return config.get(section,name)
        else:
            return default
        
    def __init__(self, plugin=None, pathCOMMANDS=None):
        self.plugin = plugin
        self.pathCOMMANDS = pathCOMMANDS

        #Legge file emoncms.ini
        config = configparser.ConfigParser()
        iniFile = '%s/%s.ini' % (self.pathCOMMANDS, plugin)
        config.read(iniFile)
        self.apikey = self.get_with_default(config=config, section="config", name="apikey", default=None)
        #self.proxy = self.get_with_default(config=config, section="network", name="proxy", default=None)
        #if self.proxy:
        #    self.proxy = {"http": self.proxy, "https": self.proxy }
        
        self.listNodes = []
        for section in config.sections():
            sectionName = section.lower()
            if sectionName[0:5] == "node_":
                dictPlugin = {}
                for (hpsuName, cloudName) in config.items(sectionName):
                    dictPlugin.update({hpsuName:cloudName})
                self.listNodes.append({"name":sectionName, "data":dictPlugin})

    def pushValues(self, vars):
        if self.plugin == "EMONCMS":
            timestamp = None
            
            for node in self.listNodes:
                nodeName = node["name"][5:]
                dictPlugin = node["data"]
                varsDict = {}
                for r in vars:
                    if not timestamp:
                        timestamp = r["timestamp"]
                    
                    hpsuName = r["name"]
                    cloudName = dictPlugin[hpsuName] if hpsuName in dictPlugin else None                

                    if cloudName:
                        varsDict.update({cloudName:r["resp"]})

                if len(varsDict) > 0:
                    varsTxt = str(varsDict).replace(" ", "")
                    _url = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=%s" % (self.apikey, timestamp, varsTxt, nodeName)                
                    
                    #r = requests.get(_url, proxies=self.proxy)
                    r = requests.get(_url)
                    
                    rc = r.text
                    if rc != "ok":
                        print ("Error pushing %s" % _url)
                    else:
                        print ("Success push:%s" % _url)
                
            return True

        if self.plugin == "DOMON":
            print ("tbd")

