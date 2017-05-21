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
logger.setLevel( logging.DEBUG )

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("can").setLevel(logging.WARNING)

com_leggi_modooperativo = "31 00 FA 01 12 00 00 00"
must_switch_off = False
must_switch_on = False
must_switch_cool_off = False
must_switch_cool_on = False
time_is_on = True
time_cool_is_on = True
id = "680"
receiver_id = int(id, 16)
temp_heat_setpoint = 21.5
temp_cool_setpoint = 25.3
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
    elif (modo_operativo == 17.0):
        etichetta = "COOLING"
    else:
        etichetta = "NOT PLANNED"
    logger.info("HPSU                : Current  mode is %s", etichetta)
    # verifica di essere nell'orario di funzionamento previsto

    now = datetime.datetime.now()
    now =  now.replace(microsecond=0)
    time_heat_start = now.replace(hour=11, minute=0, second=0, microsecond=0)
    time_heat_end = now.replace(hour=21, minute=0, second=0, microsecond=0)

    time_cool_start = now.replace(hour=20, minute=0, second=0, microsecond=0)
    now += datetime.timedelta(days=1)
    time_cool_end = now.replace(hour=7, minute=59, second=0, microsecond=0)
    now += datetime.timedelta(days=-1) 

    logger.info("SMART-THERMOSTAT    : HEATING => %s < t < %s" % (time_heat_start.strftime("%d/%m %H:%M"), time_heat_end.strftime("%d/%m %H:%M")))
    logger.info("SMART-THERMOSTAT    : COOLING => %s < t < %s" % (time_cool_start.strftime("%d/%m %H:%M"), time_cool_end.strftime("%d/%m %H:%M")))

    if ((now < time_heat_start) or (now > time_heat_end)):
        time_is_on = False
        # verifico se devo spegnere
        if (errore_lettura != True) and (modo_operativo == 3.0):
            #devo commutare da riscaldamento ad estate
            must_switch_off = True
        #sys.exit(0)

    if ((now < time_cool_start) or (now > time_cool_end)):
        time_cool_is_on = False
        # verifico se devo spegnere
        if (errore_lettura != True) and (modo_operativo == 17.0):
            #devo commutare da raffrescamento ad estate
            must_switch_cool_off = True
        #sys.exit(0)
    
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

    OEM_APIURL = 'http://emoncms.org/feed/value.json?id=36240&apikey=' + OEM_API_KEY

    try:
        r = requests.get(OEM_APIURL, timeout=5)
    except:
        logger.error(requests.exceptions.RequestException)
        sys.exit(1)

    if r.status_code != 200:
        logger.error ("Error:", r.status_code)
        sys.exit(1)

    json_umidita = r.json()

    umidita_interna = float(json_umidita)


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

    if (
           ((modo_operativo == 17.0) and (temperatura_interna < temp_cool_setpoint - temp_hyst))
           or
           must_switch_cool_off
       ) :
        # spegni mettendo in modalita' Estate
        command = "32 00 FA 01 12 05 00"
        must_switch_cool_off = True

    if (
           ((modo_operativo != 17.0) and (temperatura_interna > temp_cool_setpoint + temp_hyst))
           or
           must_switch_cool_on
       ) :
        # accendi raffrescamento mettendo in modalita' Raffrescamento
        command = "32 00 FA 01 12 11 00"
        if (modo_operativo != 3.0):
            must_switch_cool_on = True

    # 01 - Standby
    # 11 - Raffreddare
    # 04 - Ridurre
    # 03 - Riscaldare
    # 05 - Estate
    # 0b - Automatico 1
    # 0c - Automatico 2

    logger.info("SMART-THERMOSTAT    : HEATING => %02.1f °C < T Int.  < %02.1f °C" % (temp_heat_setpoint - temp_hyst, temp_heat_setpoint + temp_hyst))
    logger.info("SMART-THERMOSTAT    : COOLING => %02.1f °C < T Int.  < %02.1f °C" % (temp_cool_setpoint - temp_hyst, temp_cool_setpoint + temp_hyst))

    logger.info("OEM                 :  T Int. = %02.1f °C" % temperatura_interna)
    logger.info("OEM                 : HR Int. = %02.1f %%" % umidita_interna)

    if (must_switch_on):
        logger.info("HPSU                : Changing mode to HEATING")
    if (must_switch_off):
        logger.info("HPSU                : Changing mode to SUMMER")

    if (must_switch_cool_on):
        logger.info("HPSU                : Changing mode to COOLING")
    if (must_switch_cool_off):
        logger.info("HPSU                : Changing mode to SUMMER")

    if (must_switch_on or must_switch_off or must_switch_cool_on or must_switch_cool_off) :
        msg_data = [int(r, 16) for r in command.split(" ")]
        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            #logger.info("HPSU                : Changing heat pump mode from %s to %s" % (etichetta, msg))
            bus.send(msg)
        except Exception:
            logger.error('exception', 'Error sending msg')                    
            sys.exit(1)
