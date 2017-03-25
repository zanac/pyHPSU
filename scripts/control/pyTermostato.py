#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys, time
import datetime
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

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("can").setLevel(logging.WARNING)

com_leggi_modooperativo = "31 00 FA 01 12 00 00 00"
must_switch_off = False
must_switch_on = False
time_is_on = True
id = "680"
receiver_id = int(id, 16)
temp_heat_setpoint = 21.5
temp_cool_setpoint = 25.5
temp_hyst = 0.4

if __name__ == "__main__":    

    errore_lettura = False

    # APERTURA CONNESSIONE CAN BUS

    try:
        bus = can.interface.Bus(channel='can0', bustype='socketcan_native')
    except Exception:
        print ("exception open bus")
        sys.exit(0)

    # legge modo operativo corrente da HPSU

    if (errore_lettura != True):
        command = com_leggi_modooperativo
        msg_data = [int(r, 16) for r in command.split(" ")]

        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            bus.send(msg)
        except Exception:
            print('exception', 'Error sending msg')
            sys.exit(0)
        try:
            rcbus = bus.recv(1.0)
        except Exception:
            logger.error('exception', 'Error reading msg')
            sys.exit(0)

        modo_operativo = -10.0


        if rcbus and rcbus.data and (len(rcbus.data) >= 7) and (msg_data[2] == 0xfa and msg_data[3] == rcbus.data[3] and msg_data[4] == rcbus.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcbus.data[2]):
            modo_operativo = rcbus.data[5]

        # skippa dati sballati

        if (modo_operativo == -10.0):
            errore_lettura = True
            logger.error ("HPSU                : *** ERRORE LETTURA PARAMETRO MODO OPERATIVO CORRENTE ***")
            sys.exit(1)

    if (modo_operativo == 3.0):
        etichetta = "HEATING"
    elif (modo_operativo == 5.0):
        etichetta = "SUMMER"
    else:
        etichetta = "NOT PLANNED"
    logger.info("HPSU                : Current mode is %s", etichetta)
    # verifica di essere nell'orario di funzionamento previsto

    now = datetime.datetime.now()
    time_start = now.replace(hour=11, minute=0, second=0, microsecond=0)
    time_end = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if (now < time_start):
        logger.info("SMART-THERMOSTAT    : Planned start time = %s", time_start)
    if (now < time_end):
        logger.info("SMART-THERMOSTAT    : Planned end   time = %s", time_end)
    if ((now < time_start) or (now > time_end)):
        logger.info("SMART-THERMOSTAT    : Current time is out of planned time window")
        time_is_on = False
        # verifico se devo spegnere
        if (errore_lettura != True) and (modo_operativo != 5.0):
            #devo spegnere il riscaldamento
            must_switch_off = True

        sys.exit(0)
    
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

    if (
           ((modo_operativo == 3.0) and (temperatura_interna > temp_heat_setpoint + temp_hyst))
           or
           must_switch_off
       ) :
        # spegni mettendo in modalita' Estate
        command = "32 00 FA 01 12 05 00"
        must_switch_off = True

    if (
           ((modo_operativo != 3.0) and (temperatura_interna < temp_heat_setpoint - temp_hyst))
           or
           must_switch_on
       ) :
        # accendi riscaldamento mettendo in modalita' Riscaldamento
        command = "32 00 FA 01 12 03 00"
        if (modo_operativo != 3.0):
            must_switch_on = True

    # 01 - Standby
    # 11 - Raffreddare
    # 04 - Ridurre
    # 03 - Riscaldare
    # 05 - Estate
    # 0b - Automatico 1
    # 0c - Automatico 2

    logger.info("OEM                 : T Int. = %02.1f °C" % temperatura_interna)
    logger.info("SMART-THERMOSTAT    : Heating switch ON  threshold = %02.1f °C" % (temp_heat_setpoint - temp_hyst))
    logger.info("SMART-THERMOSTAT    : Heating switch OFF threshold = %02.1f °C" % (temp_heat_setpoint + temp_hyst))

    logger.info("SMART-THERMOSTAT    : Must switch on  is %s" % must_switch_on)
    logger.info("SMART-THERMOSTAT    : Must switch off is %s" % must_switch_off)

    if (must_switch_on or must_switch_off) :
        msg_data = [int(r, 16) for r in command.split(" ")]
        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            logger.info("HPSU                : Changing heat pump mode from %s to %s" % (etichetta, msg))
            bus.send(msg)
        except Exception:
            logger.error('exception', 'Error sending msg')                    
            sys.exit(1)
