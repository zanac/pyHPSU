#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys, time
try:
    import can
except Exception:
    pass


import logging
import logging.handlers

logHandler = logging.handlers.TimedRotatingFileHandler("/home/pi/termostato.log",when="midnight")
logFormatter = logging.Formatter('%(asctime)s %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger()
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )

if __name__ == "__main__":    
    temp_min = float(sys.argv[1]) / 10.0
    temp_max = float(sys.argv[2]) / 10.0

    
    id = "680"
    
    receiver_id = int(id, 16)        

    # RECUPERA LA TEMPERATURA INTERNA DA OEM

    OEM_API_KEY = 'f7f5d003c595ed3285cd616521aa5aab'
    OEM_APIURL = 'http://emoncms.org/feed/value.json?id=36238&apikey=' + OEM_API_KEY

    try:
        r = requests.get(OEM_APIURL, timeout=5)
    except:
        logger.error(requests.exceptions.RequestException)
        sys.exit(1)

    if r.status_code != 200:
        logger.error ("Error:", r.status_code)
        sys.exit(1)

    json_temperature = r.json()

    temperatura_interna = float(json_temperature)

    #print (temperatura_interna, temp_min, temp_max)

    if (temperatura_interna > temp_max) :
        # spegni
        command = "32 00 FA 01 12 05 00"

    if (temperatura_interna < temp_min) :
        # accendi
        command = "32 00 FA 01 12 03 00"

    # 01 - Standby
    # 11 - Raffreddare
    # 04 - Ridurre
    # 03 - Riscaldare
    # 05 - Estate
    # 0b - Automatico 1
    # 0c - Automatico 2

    if (temperatura_interna > temp_max) or (temperatura_interna < temp_min) :
        msg_data = [int(r, 16) for r in command.split(" ")]
        logger.info("T Int. = %02.1f (C) => Cambio stato" % temperatura_interna)
        try:
            bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
        except Exception:
            logger.error ("exception open bus")
            sys.exit(1)
        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            bus.send(msg)
        except Exception:
            logger.error('exception', 'Error sending msg')                    
            sys.exit(1)
    else:
        logger.info("T Int. = %02.1f (C)" % temperatura_interna) 
