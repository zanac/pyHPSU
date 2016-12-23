#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import serial, sys, getopt, time, can

class CanPI(object):
    def __init__(self):
        self.bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
    
    def sendCommandWithID(self, cmd):
        receiver_id = int(cmd["receiver_id"], 16)
        msg_data = [int(r, 16) for r in cmd["command"].split(" ")]
        
        msg = can.Message(arbitration_id=receiver_id, data=msg_data)
        self.bus.send(msg)
        time.sleep(50.0 / 1000.0)
        timeout = 2
        rc = self.bus.recv(timeout)
        print "::::::::::::::::::::::::::"
        print str(rc)
        #todo convertire rc in stringa hex
        
        return rc
