#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
import requests
import json
import math
import binascii

import logging
import logging.handlers

logHandler = logging.handlers.TimedRotatingFileHandler("/home/pi/listener.log",when="midnight")
logFormatter = logging.Formatter('%(asctime)s %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger()
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

try:
    import can
except Exception:
    pass

# Variable Name => String (Costante)
# Signature => Hex (Costante)
# Last Read Timestamp => Time
# Last Publish Timestamp => Time
# Value [0] => Float
# Value [1] => Float
# Value [2] => Float
# Value [3] => Float
# Value [4] => Float
# Last Value => Float (corrisponde a Value [0])
# Average Value => Float (corrisponde alla media aritmetica di Value [x])
# Filtered Value => Float
# Average Filtered Value => Value

dati = [
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xF6]), "mode",            [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xFB]), "bpv",             [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0x06, 0x9B]), "posmix",          [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xF7]), "pump",            [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xFC]), "t_v1",            [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xFD]), "t_dhw1",          [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xFE]), "t_vbh",           [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC1, 0x00]), "t_r1",            [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xF9]), "ehs",             [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x62, 0x10, 0x04, 0x00, 0x00]), "t_hc_set",        [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0x03, 0x00, 0x00]), "t_dhw_set",       [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x62, 0x10, 0xFA, 0x0A, 0x0C]), "t_ext",           [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC0, 0xFF]), "t_outdoor_ot1",   [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0xC1, 0x05]), "ta2",             [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0x13, 0x00, 0x00]), "t_dhw_setpoint1", [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0x06, 0x91]), "hyst_hp",         [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0x01, 0x12]), "mode_01",         [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
    [bytes([0x32, 0x10, 0xFA, 0x01, 0xDA]), "flow_rate",       [0.0, 0.0, 0.0, 0.0, 0.0], 0.0, 0.0],
]

class CanListener(can.Listener):
    def on_message_received(self, msg):
        for i in range(len(dati)): 
            if (msg.data[0:5] == dati[i][0]):
                dati[i][2][4] =  dati[i][2][3]
                dati[i][2][3] =  dati[i][2][2]
                dati[i][2][2] =  dati[i][2][1]
                dati[i][2][1] =  dati[i][2][0]
                dati[i][2][0] =  int.from_bytes(msg.data[5:7], byteorder='big', signed=True)
                dati[i][3]    = msg.timestamp
                logger.info("%50s %05s %05s %f", msg, dati[i][1].ljust(10), dati[i][2], dati[i][3])

try:
    #can_filters = [{"can_id": "0x1c1"}]
    bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
except Exception:
    logger.error ("exception open bus")
    sys.exit(0)

a_listener = CanListener()
notifier = can.Notifier(bus, [a_listener])

logger.info("Can Logger Started")

try:
    while True:
        time.sleep(15)
        power = 1.163 * float(dati[17][2][0]) * 0.1 * ( float(dati[6][2][0]) - float(dati[7][2][0]) + 0.379 + 0.111)
        print(power)
except KeyboardInterrupt:
    bus.shutdown()
