#!/usr/bin/env python3
#
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
sys.path.append('/usr/share/pyHPSU/HPSU');
sys.path.append('/usr/share/pyHPSU/plugins');

import getopt
import time
import locale
import importlib
import logging
from HPSU import HPSU
import configparser

SocketPort = 7060


def main(argv): 
    cmd = []
    port = None
    driver = "PYCAN"
    verbose = "1"
    help = False
    output_type = "JSON"
    cloud_plugin = None
    upload = False
    lg_code = "EN"
    languages = ["EN", "IT", "DE", "NL"]
    logger = None
    conf_file = "/etc/pyHPSU/pyhpsu.conf"
    read_from_conf_file=False
    run_daemon = False
    ticker=0

    try:
        opts, args = getopt.getopt(argv,"Dhc:p:d:v:o:u:l:g:f:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type=", "upload=", "language=", "log=", "config_file="])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -D  --daemon           run as daemon')
        print('           -f  --config           Configfile, overrides given commandline arguments')
        print('           -d  --driver           driver name: [ELM327, PYCAN, EMU, HPSUD], Default: PYCAN')
        print('           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type      output type: [JSON, CSV, CLOUD] default JSON')
        print('           -c  --cmd              command: [see commands domain]')
        print('           -v  --verbose          verbosity: [1, 2]   default 1')
        print('           -u  --upload           upload on cloud: [_PLUGIN_]')
        print('           -l  --language         set the language to use [%s], default is \"EN\" ' % " ".join(languages))
        print('           -g  --log              set the log to file [_filename]')
        print('           -h  --help             show help')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-D", "--daemon"):
            run_daemon = True
        if opt in ("-f", "--config"):
            read_from_conf_file = True
            conf_file = arg        
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
        elif opt in ("-u", "--upload"):
            upload=True
            cloud_plugin = arg.upper()
        elif opt in ("-l", "--language"):
            lg_code = arg.upper()   
        elif opt in ("-g", "--log"):
            logger = logging.getLogger('domon')
            hdlr = logging.FileHandler(arg)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.ERROR)
    if verbose == "2":
        locale.setlocale(locale.LC_ALL, '')

# get config from file if given....
    if read_from_conf_file: 
        if conf_file=="":
            print("Error, please provide a config file")
            sys.exit(9)
        else:
            try:
                with open(conf_file) as f:
                    config.readfp(f)
            except IOError:
                print("Error: config file not found")	
                sys.exit(9)


        config = configparser.ConfigParser()
        config.read(conf_file)
        if config.has_option('DAEMON','PYHPSU_DEVICE'):
            driver=config['DAEMON']['PYHPSU_DEVICE']
        if config.has_option('DAEMON','PORT'):
            port=config['DAEMON']['PORT']
        if config.has_option('DAEMON','PYHPSU_LANG'):
            lg_code=config['DAEMON']['PYHPSU_LANG']
        if config.has_option('DAEMON','OUTPUT_TYPE'):
            output_type=config['DAEMON']['OUTPUT_TYPE']
        if config.has_option('DAEMON','EMONCMS'):
            cloud_plugin=config['DAEMON']['EMONCMS']

    #
    # now we should have all options...let's check them 
    #
    # Check driver 
    if driver not in ["ELM327", "PYCAN", "EMU", "HPSUD"]:
        print("Error, please specify a correct driver [ELM327, PYCAN, EMU, HPSUD] ")
        sys.exit(9)

    if driver == "ELM327" and port == "":
        print("Error, please specify a correct port for the ELM327 device ")
        sys.exit(9)

    # Check output type 
    if output_type not in ["JSON", "CSV", "CLOUD"]:
        print("Error, please specify a correct output_type [JSON, CSV, CLOUD]")
        sys.exit(9)

    # Check Plugin type
    if cloud_plugin not in ["EMONCMS"] and upload:
        print("Error, please specify a correct plugin")
        sys.exit(9)

    # Check Language
    if lg_code not in languages:
        print("Error, please specify a correct language [%s]" % " ".join(languages))
        sys.exit(9)
#
# try to query different commands in different periods
# Read them from config and group them
#
    # create dictionary for the jobs
    timed_jobs=dict()
    if read_from_conf_file and len(config.options('JOBS')):
        for each_key in config.options('JOBS'):
            job_period=config.get('JOBS',each_key)
            if not job_period in timed_jobs.keys():
                timed_jobs[job_period]=[]
            timed_jobs[job_period].append(each_key)
        wanted_periods=list(timed_jobs.keys())
    else:
        #
        # now its time to call the hpsu and do the REAL can query, but only every 2 seconds
        # and handle the data as configured
        #
        if not ticker%2:
            hpsu = read_can(driver, logger, port, cmd, lg_code)




def read_can(driver,logger,port,cmd,lg_code):
    hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
    return hpsu
    #
    # print out available commands
    #
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
   
    # really needed? Driver is checked above

    #if not driver:
    #    print("Error, please specify driver [ELM327 or PYCAN, EMU, HPSUD]")
    #    sys.exit(9)        

    arrResponse = []   
    for c in hpsu.commands:
        setValue = None
        for i in cmd:
            if ":" in i and c["name"] == i.split(":")[0]:
                setValue = i.split(":")[1]

        i = 0
        while i <= 3:
            rc = hpsu.sendCommand(c, setValue)
            if rc != "KO":            
                i = 4
                if not setValue:
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

        module = importlib.import_module("cloud")
        cloud = module.Cloud(plugin=cloud_plugin, hpsu=hpsu, logger=logger)
        cloud.pushValues(vars=arrResponse)




if __name__ == "__main__":
    global loop 
    loop=True
    while loop==True:               # run main
        main(sys.argv[1:])
        if run_daemon==false:       # if not in daemon mode, stop after one loop
            loop=False
        else:                       # else ticker +1 and sleep a second.
            ticker+=1
            time.sleep(1)