#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)
#todo: 
# output json/csv
# 
# utilizzare la formattazione del locale corrente (se ho settato Italy devo vedere date giuste, punti/virgole giusti)
# monitor mode (sniff)

import serial, sys, getopt, time, csv, locale
from hpsu import HPSU
    
    
def main(argv): 
    commands = []
    with open('pyHPSU.csv', 'rb') as csvfile:
        pyHPSUCSV = csv.reader(csvfile, delimiter=';', quotechar='"')
        next(pyHPSUCSV, None) # skip the header

        for row in pyHPSUCSV:
            commands.append({"name":row[0],
                             "desc":row[1],
                             "label":row[2],
                             "command":row[3],
                             "receiver_id":row[4],
                             "um":row[5],
                             "div":row[6]})

    cmd = []
    port = None
    driver = None
    verbose = "1"
    output_type = "JSON"
    try:
        opts, args = getopt.getopt(argv,"hc:p:d:v:o:", ["cmd=", "port=", "driver=", "verbose=", "output_type"])
    except getopt.GetoptError:
        print 'pyHPSU.py -d DRIVER -g COMMAND'
        print ' '
        print '           -d  --driver           driver name: [ELM327, PYCAN, EMU]'
        print '           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)'
        print '           -o  --output_type      output type: [JSON, CSV]   default JSON'
        print '           -c  --cmd              command: [see commands domain]'
        print '           -v  --verbose          verbosity: [1, 2]   default 1'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print "Command Name - Description"
            for cmd in commands:
                print "%12s - %s" % (cmd['name'], cmd['desc'])
            sys.exit(0)
        if opt in ("-d", "--driver"):
            driver = arg.upper()
        elif opt == "-p":
            port = arg
        elif opt in ("-c", "--cmd"):
            mode = "GET"
            cmdAppend = None
            for c in commands:
                if c["name"] == arg:
                    cmdAppend = c
            if not cmdAppend:
                print "'%s' command not exist." % arg
                sys.exit(1)

            cmd.append(cmdAppend)
        elif opt in ("-v", "--verbose"):
            verbose = arg
        elif opt in ("-o", "--output_type"):
            output_type = arg.upper()
            if output_type not in ["JSON", "CSV"]:
                print "Error, please specify a correct output_type [JSON, CSV]"
    
    if not driver:
        print "Error, please specify driver [ELM327 or PYCAN, EMU]"
        sys.exit(9)

    locale.setlocale(locale.LC_ALL, '')
    
    hpsu = HPSU(driver, port)
    
    #print datetime.datetime.now()
    
    arrResponse = []        
    for c in cmd:
        rc = hpsu.sendCommand(c)
        response = hpsu.parseCommand(cmd=c, response=rc)
        resp = hpsu.umConversion(cmd=c, response=response, verbose=verbose)
            
        #print "%s:%s" % (c["name"], hpsu.parseCommand(c, response=rc))
        arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"]})

    if output_type == "JSON":
        print arrResponse
    elif output_type == "CSV":
        print "csv"
        for r in arrResponse:
            print "%s\t%s\t%s" % (r["timestamp"], r["name"], r["resp"])

if __name__ == "__main__":
   main(sys.argv[1:])



