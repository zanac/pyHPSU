#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
try:
    import can
except Exception:
    pass

if __name__ == "__main__":    

    # 01 - Standby
    # 11 - Raffreddare
    # 04 - Ridurre
    # 03 - Riscaldare
    # 05 - Estate
    # 0b - Automatico 1
    # 0c - Automatico 2

    command = "32 00 FA 01 12 03 00"
    
    id = "680"
    
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

