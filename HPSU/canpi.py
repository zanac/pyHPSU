    #!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.3 by Vanni Brutto (Zanac)

import sys
import getopt
import time
import configparser
import logging
try:
    import can
except Exception:
    pass

class CanPI(object):
    hpsu = None
    timeout = None
    retry = None
    def __init__(self, hpsu=None):
        self.hpsu = hpsu
        try:
            self.bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
        except Exception:
            self.hpsu.printd('exception', 'Error opening bus can0')
            sys.exit(9)
            
        config = configparser.ConfigParser()
        iniFile = '%s/%s.ini' % (self.hpsu.pathCOMMANDS, "canpi")
        config.read(iniFile)
        self.timeout = float(self.get_with_default(config=config, section="config", name="timeout", default=0.05))
        self.retry = float(self.get_with_default(config=config, section="config", name="retry", default=15))
            
    
    def get_with_default(self, config, section, name, default):
        if "config" not in config.sections():
            return default
        
        if config.has_option(section,name):
            return config.get(section,name)
        else:
            return default
            
    def __del__(self):
        pass
        """try:
            self.bus.shutdown()
        except Exception:
            self.hpsu.printd('exception', 'Error shutdown canbus')"""
    
    def sendCommandWithID(self, cmd, setValue=None, priority=1):
        if setValue:
            receiver_id = 0x680
        else:
            receiver_id = int(cmd["receiver_id"], 16)
        command = cmd["command"]

        if setValue:
            command = command[:1] + '2' + command[2:]
            if command[6:8] != "FA":
                command = command[:3]+"00 FA"+command[2:8]
            command = command[:14]
            if cmd["um"] == "d":
                setValue = int(setValue)
                if setValue < 0:
                    setValue = 0x10000+setValue
                command = command+" %02X %02X" % (setValue >> 8, setValue & 0xff)
            if cmd["um"] == "i":
                setValue = int(setValue)
                command = command+" %02X 00" % (setValue)
                
        msg_data = [int(r, 16) for r in command.split(" ")]
        notTimeout = True
        i = 0
        
        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            self.bus.send(msg)
        except Exception:
            self.hpsu.printd('exception', 'Error sending msg')

        if setValue:
            return "OK"

        while notTimeout:
            i += 1
            timeout = self.timeout
            rcBUS = None
            try:
                rcBUS = self.bus.recv(timeout)
            except Exception:
                self.hpsu.printd('exception', 'Error recv')


            if rcBUS:
                if (msg_data[2] == 0xfa and msg_data[3] == rcBUS.data[3] and msg_data[4] == rcBUS.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcBUS.data[2]):
                    rc = "%02X %02X %02X %02X %02X %02X %02X" % (rcBUS.data[0], rcBUS.data[1], rcBUS.data[2], rcBUS.data[3], rcBUS.data[4], rcBUS.data[5], rcBUS.data[6])
                    notTimeout = False
                else:
                    self.hpsu.printd('error', 'SEND:%s' % (str(msg_data)))
                    self.hpsu.printd('error', 'RECV:%s' % (str(rcBUS.data)))
            else:
                self.hpsu.printd('error', 'Not aquired bus')

            if notTimeout:
                self.hpsu.printd('warning', 'msg not sync, retry: %s' % i)
                if i >= self.retry:
                    self.hpsu.printd('error', 'msg not sync, timeout')
                    notTimeout = False
                    rc = "KO"
        
        return rc
