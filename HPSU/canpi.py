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
        msg_data = [int(r, 16) for r in cmd["command"].split(" ")]
        notTimeout = True
        i = 0
        
        msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
        self.bus.send(msg)

        while notTimeout:
            i += 1
            timeout = 0.1
            rcBUS = self.bus.recv(timeout)

            if rcBUS:
                if (msg_data[2] == 0xfa and msg_data[3] == rcBUS.data[3] and msg_data[4] == rcBUS.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcBUS.data[2]):
                    rc = "%02X %02X %02X %02X %02X %02X %02X" % (rcBUS.data[0], rcBUS.data[1], rcBUS.data[2], rcBUS.data[3], rcBUS.data[4], rcBUS.data[5], rcBUS.data[6])
                    notTimeout = False
                else:
                    if i >= 15:
                        notTimeout = False
                        rc = "KO"
            else:
                if i >= 15:
                    notTimeout = False
                    rc = "KO"
        
        return rc
