#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import sys, getopt, time
import can

class CanPI(object):
    def __init__(self):
        self.bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
    
    def sendCommandWithID(self, cmd):
        receiver_id = int(cmd["receiver_id"], 16)
        
        #Provare anche togliendo il commento segutente!
        #receiver_id = receiver_id - 0x10
        msg_data = [int(r, 16) for r in cmd["command"].split(" ")]
        notTimeout = True
        i = 1
        
        
        while notTimeout:
            i += 1
            msg = can.Message(arbitration_id=receiver_id, data=msg_data)
            self.bus.send(msg)
            
            time.sleep(50.0 / 1000.0)
            timeout = 0.1
            rcBUS = self.bus.recv(timeout)
            #print (str(rcBUS.data))
            print("bus:%s:%s" % (rcBUS.arbitration_id, ("%02X %02X %02X %02X %02X %02X %02X" % (rcBUS.data[0], rcBUS.data[1], rcBUS.data[2], rcBUS.data[3], rcBUS.data[4], rcBUS.data[5], rcBUS.data[6]))))
            
            if rcBUS.arbitration_id in [receiver_id, receiver_id - 0x10]:
                rc = "%02X %02X %02X %02X %02X %02X %02X" % (rcBUS.data[0], rcBUS.data[1], rcBUS.data[2], rcBUS.data[3], rcBUS.data[4], rcBUS.data[5], rcBUS.data[6])
                notTimeout = True
            else:
                rc = "KO"
                if i >= 15:
                    notTimeout = True
        
        return rc
