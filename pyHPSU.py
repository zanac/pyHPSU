#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.4 by Vanni Brutto (Zanac)
#todo: 
# 
# utilizzare la formattazione del locale corrente (se ho settato Italy devo vedere date giuste, punti/virgole giusti)
# monitor mode (sniff)
# tcp_con = serial.serial_for_url('socket://<my_ip>:<my_port>')
#
#Lo script di lettura e pubblicazione deve essere facilmente schedulabile in modo controllato:
#- frequenza di aggiornamento (l'ideale sarebbe poterla personalizzare per singola variabile ma lasciamo stare)


import serial
import sys
import getopt
import time
import locale
import importlib
import logging
from HPSU.HPSU import HPSU

SocketPort = 7060
    
def main(argv): 
    cmd = []
    port = None
    driver = None
    verbose = "1"
    help = False
    output_type = "JSON"
    cloud_plugin = None
    lg_code = None
    languages = ["EN", "IT", "DE"]
    logger = None

    try:
        opts, args = getopt.getopt(argv,"hc:p:d:v:o:u:l:g:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type=", "upload=", "language=", "log="])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -d  --driver           driver name: [ELM327, PYCAN, EMU, HPSUD]')
        print('           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type      output type: [JSON, CSV, CLOUD] default JSON')
        print('           -c  --cmd              command: [see commands domain]')
        print('           -v  --verbose          verbosity: [1, 2]   default 1')
        print('           -u  --upload           upload on cloud: [_PLUGIN_]')
        print('           -l  --language         set the language to use [%s]' % " ".join(languages))
        print('           -g  --log              set the log to file [_filename]')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help = True
        elif opt in ("-d", "--driver"):
            driver = arg.upper()
        elif opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--cmd"):
            cmd.append(arg)
        elif opt in ("-v", "--verbose"):
            verbose = arg
        elif opt in ("-o", "--output_type"):
            output_type = arg.upper()
            if output_type not in ["JSON", "CSV", "CLOUD"]:
                print("Error, please specify a correct output_type [JSON, CSV, CLOUD]")
                sys.exit(9)
        elif opt in ("-u", "--upload"):
            cloud_plugin = arg.upper()
            if cloud_plugin not in ["EMONCMS"]:
                print("Error, please specify a correct plugin")
                sys.exit(9)
        elif opt in ("-l", "--language"):
            lg_code = arg.upper()   
            if lg_code not in languages:
                print("Error, please specify a correct language [%s]" % " ".join(languages))
                sys.exit(9)
        elif opt in ("-g", "--log"):
            logger = logging.getLogger('domon')
            hdlr = logging.FileHandler(arg)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.ERROR)
    if verbose == "2":
        locale.setlocale(locale.LC_ALL, '')
        
    hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
    
    if help:
        if len(cmd) == 0:
            print("List available commands:")
            print("%12s - %-10s" % ('COMMAND', 'LABEL'))
            print("%12s---%-10s" % ('------------', '----------'))
            for cmd in hpsu.listCommands:
                print("%12s - %-10s" % (cmd['name'], cmd['label']))
        else:
            print("%12s - %-10s - %s" % ('COMMAND', 'LABEL', 'DESCRIPTION'))
            print("%12s---%-10s---%s" % ('------------', '----------', '---------------------------------------------------'))
            for c in hpsu.commands:
                print("%12s - %-10s - %s" % (c['name'], c['label'], c['desc']))
        sys.exit(0)

    if not driver:
        print("Error, please specify driver [ELM327 or PYCAN, EMU, HPSUD]")
        sys.exit(9)        

    arrResponse = []        
    for c in hpsu.commands:
        i = 0
        while i <= 3:
            rc = hpsu.sendCommand(c)
            if rc != "KO":
                i = 4
                response = hpsu.parseCommand(cmd=c, response=rc, verbose=verbose)
                resp = hpsu.umConversion(cmd=c, response=response, verbose=verbose)

                arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"]})
            else:
                i += 1
                time.sleep(2.0)
                hpsu.printd('warning', 'retry %s command %s' % (i, c["name"]))
                if i == 4:
                    hpsu.printd('error', 'command %s failed' % (c["name"]))

    if output_type == "JSON":
        print(arrResponse)
    elif output_type == "CSV":
        for r in arrResponse:
            print("%s\t%s\t%s" % (r["timestamp"], r["name"], r["resp"]))
    elif output_type == "CLOUD":
        if not cloud_plugin:
            print ("Error, please specify a cloud_plugin")
            sys.exit(9)

        module = importlib.import_module("plugins.cloud")
        cloud = module.Cloud(plugin=cloud_plugin, hpsu=hpsu, logger=logger)
        cloud.pushValues(vars=arrResponse)
        

if __name__ == "__main__":
    main(sys.argv[1:])
