#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
try:
    import can
except Exception:
    pass

if __name__ == "__main__":    
    temp = sys.argv[1:]
    if len(temp) == 0:
        print("passare temperatura su command line in formato 'gradi * 10', esempio 210 = 21,0 gradi")
        sys.exit(0)
    
    if int(temp[0]) < 100:
        print("sicuro che stai passando la temperatura moltiplicata 10???? 210 = 21 gradi!!! Emiliano ocio!")
        sys.exit(0)
    tempHex = "%02x" % int(temp[0])
    
    #command = "62 00 05 00 %s 00 00" % tempHex
    #command = "62 00 05 00 %s 00 00" % tempHex
    #command = "62 0a 05 00 %s 00 00" % tempHex
    #command = "60 0a 05 00 %s 00 00" % tempHex
    command = "32 00 FA 00 05 00 %s" % tempHex    
    
    id = "680" #provare con 11a? oppure 190? oppure 310?
    
    receiver_id = int(id, 16)        
    msg_data = [int(r, 16) for r in command.split(" ")]
    
    try:
        bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
    except Exception:
        print ("exception open bus")
        sys.exit(0)

    try:
        msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
        bus.send(msg)
    except Exception:
        print('exception', 'Error sending msg')                    
        sys.exit(0)

