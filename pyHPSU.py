#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.2 by Vanni Brutto (Zanac)
#todo: 
# output json/csv
# 
# utilizzare la formattazione del locale corrente (se ho settato Italy devo vedere date giuste, punti/virgole giusti)
# monitor mode (sniff)

import serial, sys, getopt, time, locale
from hpsu import HPSU
    
    
def main(argv): 
    cmd = []
    port = None
    driver = None
    verbose = "1"
    help = False
    output_type = "JSON"
    try:
        opts, args = getopt.getopt(argv,"hc:p:d:v:o:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type"])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -d  --driver           driver name: [ELM327, PYCAN, EMU]')
        print('           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type      output type: [JSON, CSV]   default JSON')
        print('           -c  --cmd              command: [see commands domain]')
        print('           -v  --verbose          verbosity: [1, 2]   default 1')
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
            if output_type not in ["JSON", "CSV"]:
                print("Error, please specify a correct output_type [JSON, CSV]")

    locale.setlocale(locale.LC_ALL, '')
        
    hpsu = HPSU(driver=driver, port=port, cmd=cmd)
    
    if help:
        if len(cmd) == 0:
            print("List available commands:")
            strCommands = ""
            for cmd in hpsu.listCommands:
                strCommands = ("%s%s " % (strCommands, cmd['name']))
            print(strCommands)
        else:
            for c in hpsu.commands:
                print("%12s - %s" % (c['name'], c['desc']))
        sys.exit(0)

    if not driver:
        print("Error, please specify driver [ELM327 or PYCAN, EMU]")
        sys.exit(9)        

    arrResponse = []        
    for c in hpsu.commands:
        rc = hpsu.sendCommand(c)
        response = hpsu.parseCommand(cmd=c, response=rc)
        resp = hpsu.umConversion(cmd=c, response=response, verbose=verbose)
            
        arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"]})

    if output_type == "JSON":
        print(arrResponse)
    elif output_type == "CSV":
        for r in arrResponse:
            print("%s\t%s\t%s" % (r["timestamp"], r["name"], r["resp"]))

if __name__ == "__main__":
    main(sys.argv[1:])