#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
import requests
import json
import math
import binascii
#import statistics
import struct

import logging
import logging.handlers

from collections import deque
import itertools
from scipy.signal import butter, filtfilt
import numpy as np

logHandler = logging.handlers.TimedRotatingFileHandler("/home/pi/listener.log",when="midnight")
logFormatter = logging.Formatter('%(asctime)s %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger()
logger.addHandler( logHandler )
logger.setLevel( logging.ERROR )

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

try:
    import can
except Exception:
    pass

# Variable Name => String (Costante)
# CAN Signature => Hex (Costante)
# [Timestamp, Value] Vector => Float
# Last Publish Timestamp => Time
# Average Value => Float (corrisponde alla media aritmetica di Value [x])

dati = [
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xF6]), deque([], 400), deque([], 400), "_mode", False],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xFB]), deque([], 400), deque([], 400), "_bpv", False],
    [bytearray([0x32, 0x10, 0xFA, 0x06, 0x9B]), deque([], 400), deque([], 400), "_posmix", False],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xF7]), deque([], 400), deque([], 400), "_pump", False],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xFC]), deque([], 400), deque([], 400), "_t_v1", True],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xFD]), deque([], 400), deque([], 400), "_t_dhw1", True],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xFE]), deque([], 400), deque([], 400), "_t_vbh", True],
    [bytearray([0x32, 0x10, 0xFA, 0xC1, 0x00]), deque([], 400), deque([], 400), "_t_r1", True],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xF9]), deque([], 400), deque([], 400), "_ehs", False],
    [bytearray([0x62, 0x10, 0x04]), deque([], 400), deque([], 400), "_t_hc_set", False],
    [bytearray([0x32, 0x10, 0x03]), deque([], 400), deque([], 400), "_t_dhw_set", False],
    [bytearray([0x62, 0x10, 0xFA, 0x0A, 0x0C]), deque([], 400), deque([], 400), "_t_ext", False],
    [bytearray([0x32, 0x10, 0xFA, 0xC0, 0xFF]), deque([], 400), deque([], 400), "_t_outdoor_ot1", False],
    [bytearray([0x32, 0x10, 0xFA, 0xC1, 0x05]), deque([], 400), deque([], 400), "_ta2", False],
    [bytearray([0x32, 0x10, 0x13]), deque([], 400), deque([], 400), "_t_dhw_setpoint1", False],
    [bytearray([0x32, 0x10, 0xFA, 0x06, 0x91]), deque([], 400), deque([], 400), "_hyst_hp", False],
    [bytearray([0xd2, 0x10, 0xFA, 0x01, 0x12]), deque([], 400), deque([], 400), "_mode_01", False],
    [bytearray([0x32, 0x10, 0xFA, 0x01, 0xDA]), deque([], 400), deque([], 400), "_flow_rate", True],
    [bytearray([0x32, 0x10, 0xFA, 0xC1, 0x03]), deque([], 400), deque([], 400), "_tliq2", False],
    [bytearray([0x32, 0x10, 0xFA, 0x09, 0x1C]), deque([], 400), deque([], 400), "_qboh", False],
    [bytearray([0x32, 0x10, 0xFA, 0x09, 0x20]), deque([], 400), deque([], 400), "_qchhp", False],
    [bytearray([0x32, 0x10, 0xFA, 0x06, 0xA7]), deque([], 400), deque([], 400), "_qch", False],
    [bytearray([0x32, 0x10, 0xFA, 0x09, 0x30]), deque([], 400), deque([], 400), "_qwp", False],
    [bytearray([0x32, 0x10, 0xFA, 0x09, 0x2C]), deque([], 400), deque([], 400), "_qdhw", False],
    [bytearray([0x22, 0x10, 0xFA, 0xC0, 0xB4]), deque([], 400), deque([], 400), "_water_pressure", False]
]

b, a = butter(5, 1, btype='low', analog=False)

class CanListener(can.Listener):
    def on_message_received(self, msg):
        logger.debug("MSG Received")
        found = False
        for i in range(len(dati)): 
            lungh = len(dati[i][0])
            #logger.debug("%d %s %s", lungh, binascii.hexlify(msg.data[2:lungh]),  binascii.hexlify(dati[i][0][2:lungh]))
            if (msg.data[2:lungh] == dati[i][0][2:lungh]):
                found = True

                if (msg.data[0:1] == dati[i][0][0:1]):
                    # dati nativi dai sensori

                    nuovo_dato = struct.unpack(">h", msg.data[lungh:lungh+2])[0]

                    # filtri ad-hoc

                    # rimuove i buchi di misura sul flow_rate in base al valore di mode

                    if ((nuovo_dato == 0) and (i == 17) and (len(dati[0][1]) > 0) and
                       (dati[0][1][-1] != 0) and (len(dati[i][1]) > 0)):
                        dati[i][1].append(dati[i][1][-1])
                    else:
                        dati[i][1].append(nuovo_dato)

                    if ((dati[i][4] == True) and (len(dati[i][1]) > 18)):

                        ultimi_10 = list(itertools.islice(dati[i][1], len(dati[i][1]) - 11, len(dati[i][1]) - 1))
                        logger.debug("%4d %19s => %10s %200s", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), ultimi_10)
                        dati[i][2].append(np.mean(ultimi_10))
                        y = filtfilt(b, a, dati[i][1])
                        logger.info("%4d %19s => %10s %200s %d", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), y, len(y))
                    else:
                        dati[i][2].append(dati[i][1][-1])

                    logger.debug(binascii.hexlify(msg.data))

                    logger.info("%4d %19s => %10s %10s", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), dati[i][1])
                    logger.info("%4d %19s => %10s %10s %d", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), dati[i][2], nuovo_dato)

                    OEM_API_KEY = '3f31332ec065af95bdcfec650899febd'

                    valore = {}
                    logger.debug(nuovo_dato)
                    logger.debug(dati[i][1][-1])
                    logger.debug(dati[i][2][-1])
                    valore[dati[i][3]] = round(float(dati[i][2][-1]), 2)
                    valore_json = json.dumps(valore)

                    OEM_APIURL = "https://emoncms.org/api/post?apikey=%s&time:%s&json=%s&node=999" % (OEM_API_KEY, msg.timestamp, valore_json)

                    logger.info("%4d %19s => %10s POSTING TO EMONCMS %s", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), valore_json)

                    try:
                        r = requests.get(OEM_APIURL, timeout=5)
                    except:
                        logger.error(requests.exceptions.RequestException)

                else:
                    logger.debug("%4d %19s => %10s READ REQUEST %s %s",  msg.arbitration_id, binascii.hexlify(msg.data).ljust(19), dati[i][3].ljust(15), binascii.hexlify(msg.data[0:2]), binascii.hexlify(dati[i][0][0:2]))
                break
        if (found == False):
            logger.debug("%4d %19s => UNKNOWN", msg.arbitration_id, binascii.hexlify(msg.data).ljust(19))


try:
    #can_filters = [{"can_id": "0x1c1"}]
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
except Exception:
    logger.error ("exception open bus")
    sys.exit(0)

a_listener = CanListener()
notifier = can.Notifier(bus, [a_listener])

logger.info("Can Logger Started")

#logger.debug(dati[0])

#for i in range(len(dati)):
#    time.sleep(1)
#    logger.debug(i)
#    msg = can.Message(arbitration_id=0x190, data=dati[i][0], extended_id=False, dlc=7)
#    logger.debug(msg)
#    bus.send(msg)

try:
    while True:
        time.sleep(1)
        #power = 1.163 * float(dati[17][2][0]) * 0.1 * ( float(dati[6][2][0]) - float(dati[7][2][0]) + 0.379 + 0.111)
        # print(power)
        #logger.debug("Alive !")
except KeyboardInterrupt:
    bus.shutdown()
