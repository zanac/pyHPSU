#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
import requests
import json
import math

import logging
import logging.handlers

logHandler = logging.handlers.TimedRotatingFileHandler("/home/pi/mandata.log",when="midnight")
logFormatter = logging.Formatter('%(asctime)s %(message)s')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger()
logger.addHandler( logHandler )
logger.setLevel( logging.INFO )

#logging.basicConfig(filename='/home/pi/mandata.log',level=logging.INFO, format='%(asctime)s %(message)s')

try:
    import can
except Exception:
    pass

# calcola il valore medio sugli ultimi 3 campioni

def get_smooth(x):
  if not hasattr(get_smooth, "t"):
    get_smooth.t = [x,x,x,x]
  get_smooth.t[3] = get_smooth.t[2]
  get_smooth.t[2] = get_smooth.t[1]
  get_smooth.t[1] = get_smooth.t[0]
  get_smooth.t[0] = x
  xs = (get_smooth.t[0]+get_smooth.t[1]+get_smooth.t[2]+get_smooth.t[3])/4
  return(xs)

# COSTANTI

# dati Daikin HPSU Compact
# temperatura esterna, potenza al 100%, COP al 50%
potenza_nominale=[[12,9.20,7.65],[11,9.06,7.33],[10,8.91,7.01],[9,8.77,6,69],[8,8.62,6.37],[7,8.48,6.05],[6,8.10,5.74],[5,7.72,5.43],[4,7.34,5.13],[3,6.96,4.82],[2,6.58,4.51],[1,6.47,4.33],[0,6.37,4.14],[-1,6.26,3.96],[-2,6.15,3.77],[-3,6.02,3.70],[-4,5.88,3.63],[-5,5.75,3.56],[-6,5.61,3.49],[-7,5.48,3.42]]

temperatura_interna_nominale = 21.5
ore_funzionamento = 13.0
Kp = 0.5
Dt = 60000.0
Ki = 1 / 108000000.0 * Kp

portata = 800.0

id = "680"
receiver_id = int(id, 16)

com_scrivi_mandata      = "32 00 FA 00 05 %s 00"
com_leggi_testerna      = "31 00 FA C0 FF 00 00 00"
com_leggi_tritorno      = "31 00 FA C1 00 00 00 00"
com_leggi_modooperativo = "31 00 FA 01 12 00 00 00"
com_leggi_mode          = "31 00 FA C0 F6 00 00 00"

# RECUPERA LA TEMPERATURA MEDIA PREVISTA PER LE PROSSIME 24 ORE DA WU

WU_API_KEY = '14cd099d84ae0366'
WU_COUNTRY = 'Italy'
WU_LOCATION = 'Vigevano'
WU_APIURL = 'http://api.wunderground.com/api/' + WU_API_KEY + '/hourly/q/' + WU_COUNTRY + '/' + WU_LOCATION + '.json'

try:
    r = requests.get(WU_APIURL, timeout=5)
except:
    logger.error(requests.exceptions.RequestException)

if r.status_code != 200:
  logger.error ("Error:", r.status_code)

json_weather = r.json()
conta = 0
temperatura_esterna_24ore = 0.0
temperatura_esterna = []
ind_ora_max = 0
temperatura_max = 0.0
temperatura_min = 0.0
temperatura_WU = 0.0

for previsione_oraria in json_weather['hourly_forecast']:
    if (conta < 36):
        temperatura_WU = float(previsione_oraria['temp']['metric'].replace(u'\N{MINUS SIGN}', '-'))
        if (conta < 24) :
            temperatura_esterna_24ore += temperatura_WU
            if (temperatura_WU > temperatura_max):
                temperatura_max = temperatura_WU
                ind_ora_max = conta + 1
            if (temperatura_WU < temperatura_min):
                temperatura_min = temperatura_WU
        temperatura_esterna.append([int(previsione_oraria['FCTTIME']['hour']), float(previsione_oraria['temp']['metric'].replace(u'\N{MINUS SIGN}', '-'))])
        conta += 1

temperatura_esterna_24ore /= 24.0

#print (temperatura_esterna)

logger.info (ind_ora_max, temperatura_esterna[ind_ora_max])

#calcolo il fabbisogno di energia termica per le prossime 24 ore

energia_termica =  66.11 * 114.35 * (temperatura_interna_nominale - temperatura_esterna_24ore) / 2544.0

#determino la potenza termica in base al fabbisogno termico suddiviso su 22.0 ore di funzionamento; non deve scendere sotto il 30% come regime di funzionamento

potenza_termica = max(energia_termica / 22.0, 0.35 * potenza_nominale[max(12 - round(temperatura_esterna_24ore), 0)][1])

ore_funzionamento = min(round (energia_termica / potenza_termica), 24.0)

logger.info ("METEO+INVOLUCRO      : T Esterna = %02.1f C => E Termica = %02.1f kWh => P t media = %01.2f kW su %02.0f ore" % (temperatura_esterna_24ore, energia_termica, potenza_termica, ore_funzionamento))

ind_ora_start = ind_ora_max
ind_ora_end = ind_ora_max

while (ind_ora_end - ind_ora_start < ore_funzionamento) :
    if (ind_ora_start >= 2) and (ind_ora_end < 35):
        if (potenza_nominale[max(12-round(temperatura_esterna[ind_ora_start-1][1]),0)][2] > potenza_nominale[max(12-round(temperatura_esterna[ind_ora_end+1][1]),0)][2]) :
        #if (temperatura_esterna[ind_ora_start - 1][1] > temperatura_esterna[ind_ora_end + 1][1]) :
            ind_ora_start -= 1
        else :
            ind_ora_end += 1
    else :
        if (ind_ora_end < 35) :
            ind_ora_end += 1
        else :
            ind_ora_start -= 1
    logging.info ("METEO      : ", ind_ora_start, temperatura_esterna[ind_ora_start], potenza_nominale[max(12-round(temperatura_esterna[ind_ora_start][1]),0)][2], ind_ora_end, temperatura_esterna[ind_ora_end], potenza_nominale[max(12-round(temperatura_esterna[ind_ora_end][1]),0)][2])

ora_start = temperatura_esterna[ind_ora_start][0]

ora_end = temperatura_esterna[ind_ora_end][0]

#print (ora_start, ora_end, ore_funzionamento)

indice = ind_ora_start
energia_termica_actual=0.0
potenza_termica_corrente=0.0

while (indice < ind_ora_end) :
    potenza_termica_corrente = min(max(0.3 * potenza_nominale[max(12 - round(temperatura_esterna[indice][1]), 0)][1], potenza_termica), 0.7 * potenza_nominale[max(12 - round(temperatura_esterna[indice][1]), 0)][1])
    energia_termica_actual += potenza_termica_corrente
    logger.info("METEO+HPSU           : #%2d => %2s:00 => %2.0f C => P t nom. %1.2f kW (30%%) %1.2f kW (70%%) => Pt = %1.2f kW ; COP 50%% = %01.2f" %
        (
            indice - ind_ora_start + 1,
            temperatura_esterna[indice][0],
            temperatura_esterna[indice][1],
            0.3 * potenza_nominale[max(12 - round(temperatura_esterna[indice][1]), 0)][1],
            0.7 * potenza_nominale[max(12 - round(temperatura_esterna[indice][1]), 0)][1],
            potenza_termica_corrente,
            potenza_nominale[max(12 - round(temperatura_esterna[indice][1]), 0)][2]
        )
    )
    indice += 1

#logger.info ("Energia termica effettiva = %2.1f kWh" % energia_termica_actual)
# INIZIALIZZAZIONE VARIABILI CONTROLLER PI

Integrale = 0.0

# LOOP PRINCIPALE

temperatura_esterna_last = -1000.0
modo_operativo_last = 0.0
mode_last = 0.0
temperatura_mandata_nominale_round_last = 0.0
temperatura_mandata_nominale_last = 0.0

while (1):

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
            modo_operativo = modo_operativo_last
            errore_lettura = True
            #print("*** ERRORE LETTURA HPSU ***")
        else:
            modo_operativo_last = modo_operativo 

    # legge mode corrente da HPSU

    if (errore_lettura != True) and (modo_operativo == 3.0):
        command = com_leggi_mode
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
            print('exception', 'Error reading msg')
            sys.exit(0)

        mode = -10.0

        if rcbus and rcbus.data and (len(rcbus.data) >= 7) and (msg_data[2] == 0xfa and msg_data[3] == rcbus.data[3] and msg_data[4] == rcbus.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcbus.data[2]):
            mode = rcbus.data[6]

        # skippa dati sballati

        if (mode == -10.0):
            mode = mode_last
            errore_lettura = True
            #print("*** ERRORE LETTURA HPSU ***")
        else:
            mode_last = mode

    # legge temperatura ritorno corrente da HPSU

    if (errore_lettura != True) and (modo_operativo == 3.0):
        command = com_leggi_tritorno
        msg_data = [int(r, 16) for r in command.split(" ")]

        try:
            msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
            bus.send(msg)
        except can.CanError:
            logger.error('exception', 'Error sending msg')
            sys.exit(0)
        try:
            rcbus = bus.recv(1.0)
        except can.CanError:
            logger.error('exception', 'Error reading msg')
            sys.exit(0)

        temperatura_ritorno = 0.0

        if rcbus and rcbus.data and (len(rcbus.data) >= 7) and (msg_data[2] == 0xfa and msg_data[3] == rcbus.data[3] and msg_data[4] == rcbus.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcbus.data[2]):
            temperatura_ritorno = (rcbus.data[6] + rcbus.data[5] * 256) / 10.0

        # skippa e filtra dati sballati

        if (temperatura_ritorno <= 15.0):
            temperatura_ritorno = 26.0
            errore_lettura = True
        else:
            # se il valore letto e' valido, faccio la media mobile sugli ultimi 4 campioni
            temperatura_ritorno = get_smooth(temperatura_ritorno)

        # smorzo le variazioni repentine poiche' la sonda della temperatura di ritorno e' rumorosa

        # if (temperatura_ritorno_last != -1000.0) and (math.fabs(temperatura_ritorno - temperatura_ritorno_last) < 2.5):
        #    temperatura_ritorno = (temperatura_ritorno + temperatura_ritorno_last) / 2.0
        #    temperatura_ritorno_last = temperatura_ritorno

    # legge temperatura esterna corrente da HPSU

    if (errore_lettura != True) and (modo_operativo == 3.0):
        command = com_leggi_testerna
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
            print('exception', 'Error reading msg')
            sys.exit(0)

        temperatura_esterna = -1000.0

        if rcbus and rcbus.data and (len(rcbus.data) >= 7) and (msg_data[2] == 0xfa and msg_data[3] == rcbus.data[3] and msg_data[4] == rcbus.data[4]) or (msg_data[2] != 0xfa and msg_data[2] == rcbus.data[2]):
            temperatura_esterna = (rcbus.data[6] + rcbus.data[5] * 256) / 10.0

        # skippa dati sballati

        if ((temperatura_esterna < -20.0) or (temperatura_esterna > 45.0)):
            temperatura_esterna = temperatura_esterna_last
            errore_lettura = True
            #print("*** ERRORE LETTURA HPSU ***")
        else:
            if (temperatura_esterna_last != -1000.0):
                temperatura_esterna = (temperatura_esterna + temperatura_esterna_last) / 2.0
            temperatura_esterna_last = temperatura_esterna

    # RECUPERA LA TEMPERATURA INTERNA DA OEM

    if (errore_lettura != True) and (modo_operativo == 3.0):
        OEM_API_KEY = 'f7f5d003c595ed3285cd616521aa5aab'
        OEM_APIURL = 'http://emoncms.org/feed/value.json?id=36238&apikey=' + OEM_API_KEY

        try:
            r = requests.get(OEM_APIURL, timeout=5)
        except:
            errore_lettura = True
            logger.error(requests.exceptions.RequestException)

        if r.status_code != 200:
            logger.error ("Error:", r.status_code)
        else:
            json_temperature = r.json()
            temperatura_interna = float(json_temperature)
            logger.info ("OEM                  : T Int = %02.1f C" % temperatura_interna)

    # faccio l'elaborazione solo se la HPSU e' in modalita' riscaldamento e non ci sono stati errori tecnici di lettura dei dati
    if (errore_lettura != True) and (modo_operativo == 3.0):

        # calcola i limiti di potenza termica (e Delta T) alla temperatura esterna corrente
        potenza_nominale_100 = potenza_nominale[12 - round(temperatura_esterna)][1]
        potenza_nominale_30 = 0.3 * potenza_nominale_100
        potenza_nominale_70 = 0.6 * potenza_nominale_100
        logger.info("HPSU                 : TA = %02.1f C => P Nom  (kW) @30%% = %02.2f @70%% = %02.2f @100%% = %02.2f" % (temperatura_esterna, potenza_nominale_30, potenza_nominale_70, potenza_nominale_100))

        # applico sia i limiti di potenza che il limite di Delta T compreso tra 3 ed 8 gradi
        # ho alzato arbitrariamente il valore minimo a 3.5 C
        delta_t_minimo = max(potenza_nominale_30 / (1.163 * portata) * 1000.0, 1.5)
        delta_t_massimo = min(potenza_nominale_70 / (1.163 * portata) * 1000.0, 8.0)
        logger.info("HPSU                 : TA = %02.1f C => Delta T (C) @30%% = %02.2f @70%% = %02.2f" % (temperatura_esterna, delta_t_minimo, delta_t_massimo))

        # verifica di non essere in modalita' corrente raffrescamento
        if ((mode == 0.0) or (mode == 1.0) or (mode == 3.0) or (mode == 4.0)) :

            # inizio elaborazione controller PI
            Errore = temperatura_interna_nominale - temperatura_interna
            if (Errore > 5.0) or (Errore < -5.0) :
                logger.error ("ERRORE TROPPO GRANDE !!!")
                sys.exit(0)
            
            # aggiorno l'integrale del controller PI solo se c'e' comando di compressore acceso
            if (mode == 1.0):
                Integrale += Errore * Dt
            OutputPI = Kp * Errore + Ki * Integrale

            # centro il controller PI sul valore atteso di potenza termica data la previsione di temperatura esterna, fabbisogno termico, numero ore di funzionamento
            delta_t = 1000.0 * potenza_termica / (1.163 * portata) + (delta_t_massimo - delta_t_minimo) * OutputPI
               
            # verifico che il DeltaT stimato sia all'interno dei limiti calcolati in precedenza
            delta_t = min(max(delta_t_minimo, delta_t), delta_t_massimo)

            # limito la temperatura di mandata nominale calcolata ad un valore massimo di 35.0 C
            temperatura_mandata_nominale = min(temperatura_ritorno + delta_t, 35.0)

            # smorzo le variazioni repentine mediando gli ultimi due campioni disponibili (la temperatura di ritorno e' molto rumorosa)
            temperatura_mandata_nominale_round = round ((temperatura_mandata_nominale) * 2.0)/ 2.0

            # con compressore spento incremento la mandata nominale di 1.5 C per far ripartire prima il compressore ma senza esagerare
            if ((mode == 0.0) and (temperatura_mandata_nominale_round_last != 0.0)):
                if (mode_last != 0.0):
                    temperatura_mandata_nominale_round = temperatura_mandata_nominale_round_last + 1.5
                else:
                    temperatura_mandata_nominale_round = temperatura_mandata_nominale_round_last

            logger.info ("CONTROLLER PI + HPSU : TR = %02.1f C ; Target T-HC Setpoint %2.2f C" % (temperatura_ritorno, temperatura_mandata_nominale_round))

            # smorzo le variazioni repentine di mandata nominale (solo quando sono entro i limiti di funzionamento della pompa di calore)
            #if ((temperatura_mandata_nominale_round_last != 0.0) and ((temperatura_mandata_nominale_round - temperatura_ritorno) <= delta_t_massimo)):
            #    temperatura_mandata_nominale_round = min(max(temperatura_mandata_nominale_round, temperatura_mandata_nominale_round_last - 0.5), temperatura_mandata_nominale_round_last + 0.5)

            logger.info ("CONTROLLER PI        : Integrale = %9.1f ; Errore = %1.2f ; Output PI = %1.6f ; Delta T nom = %2.2f (C) ; Delta T teo = %2.2f (C)" % (Integrale, Errore, OutputPI, delta_t, 1000.0 * potenza_termica / (1.163 * portata)))

            if ((temperatura_mandata_nominale_round_last == 0.0) or
               (temperatura_mandata_nominale_round != temperatura_mandata_nominale_round_last)):
                intero = int (temperatura_mandata_nominale_round * 10)
                #print ("gino", intero)
                alto = intero >> 8
                basso = intero & 255
                #print (alto, basso)
                tempHex = "%02x %02x" % (alto, basso)

                #print (tempHex)

                command = com_scrivi_mandata % tempHex

                #print (command)

                msg_data = [int(r, 16) for r in command.split(" ")]

                try:
                    msg = can.Message(arbitration_id=receiver_id, data=msg_data, extended_id=False, dlc=7)
                    bus.send(msg)
                except Exception:
                    print('exception', 'Error sending msg')
                    sys.exit(0)
            
                logger.info ("CONTROLLER PI + HPSU : Modo Oper. = %01.0f ; Mode = %01.0f ; TR = %02.1f C ; Changing T-HC Setpoint from %2.2f to %2.2f C (would be %2.2f C)" % (modo_operativo, mode, temperatura_ritorno, temperatura_mandata_nominale_round_last, temperatura_mandata_nominale_round, temperatura_mandata_nominale))

                temperatura_mandata_nominale_round_last = temperatura_mandata_nominale_round

        else:
            logger.info ("CONTROLLER PI + HPSU : Modo Oper. = %01.0f ; Mode = %01.0f ; TR = %02.1f C" % (modo_operativo, mode, temperatura_ritorno))

        #print("alive")
        time.sleep(40)
    else:
        if (errore_lettura != True):
            logger.error ("CONTROLLER PI + HPSU : MODALITA' RISCALDAMENTO OFF")
            time.sleep(40)
        else:
            logger.error ("CONTROLLER PI + HPSU : *** ERRORE LETTURA DA HPSU ***")
            time.sleep(1)
