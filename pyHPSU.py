#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-


import serial
import sys
#sys.path.append('/usr/share/pyHPSU/HPSU')
#sys.path.append('/usr/share/pyHPSU/plugins')
import os
import getopt
import time
import locale
import importlib
import logging
from HPSU.HPSU import HPSU
import configparser
import threading
import csv
import json

SocketPort = 7060

def main(argv):
    cmd = []
    port = None
    driver = "PYCAN"
    verbose = "1"
    show_help = False
    output_type = "JSON"
    upload = False
    lg_code = "EN"
    languages = ["EN", "IT", "DE", "NL"]
    logger = None
    pathCOMMANDS = "/etc/pyHPSU"
    global conf_file
    conf_file = None
    global default_conf_file
    default_conf_file = "/etc/pyHPSU/pyhpsu.conf"
    read_from_conf_file=False
    global auto
    global ticker
    ticker=0
    loop=True
    auto=False
    #commands = []
    #listCommands = []
    global config
    config = configparser.ConfigParser()
    global n_hpsu
    env_encoding=sys.stdout.encoding
    PLUGIN_PATH="/usr/lib/python3/dist-packages/HPSU/plugins"
    backup_mode=False
    global backup_file
    restore_mode=False
    global options_list
    options_list={}
    #
    # get all plugins
    #
    PLUGIN_LIST=["JSON", "CSV", "BACKUP"]
    PLUGIN_STRING="JSON, CSV, BACKUP"
    for file in os.listdir(PLUGIN_PATH):
        if file.endswith(".py") and not file.startswith("__"):
            PLUGIN=file.upper().split(".")[0]
            PLUGIN_STRING+=", "
            PLUGIN_STRING+=PLUGIN
            PLUGIN_LIST.append(PLUGIN)

    try:
        opts, args = getopt.getopt(argv,"ahc:p:d:v:o:l:g:f:b:r:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type=", "upload=", "language=", "log=", "config_file="])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -a  --auto            do atomatic queries')
        print('           -f  --config          Configfile, overrides given commandline arguments')
        print('           -d  --driver          driver name: [ELM327, PYCAN, EMU, HPSUD], Default: PYCAN')
        print('           -p  --port            port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type     output type: [' + PLUGIN_STRING + '] default JSON')
        print('           -c  --cmd             command: [see commands domain]')
        print('           -v  --verbose         verbosity: [1, 2]   default 1')
        print('           -l  --language        set the language to use [%s], default is \"EN\" ' % " ".join(languages))
        print('           -b  --backup          backup configurable settings to file [filename]')
        print('           -r  --restore         restore HPSU settings from file [filename]')
        print('           -g  --log             set the log to file [_filename]')
        print('           -h  --help            show help')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-a", "--auto"):
            auto = True
            options_list["auto"]=""

        if opt in ("-f", "--config"):
            read_from_conf_file = True
            conf_file = arg
            options_list["config"]=arg
           
        if opt in ("-b", "--backup"):
            backup_mode=True
            backup_file = arg
            output_type = "BACKUP" 
            options_list["backup"]=arg

        if opt in ("-r", "--restore"):
            restore_mode=True
            backup_file = arg
            options_list["restore"]=arg

        if opt in ("-h", "--help"):
            show_help = True
            options_list["help"]=""

        elif opt in ("-d", "--driver"):
            driver = arg.upper()
            options_list["driver"]=arg.upper()

        elif opt in ("-p", "--port"):
            port = arg
            options_list["port"]=arg

        elif opt in ("-c", "--cmd"):
            cmd.append(arg)

        elif opt in ("-v", "--verbose"):
            verbose = arg
            options_list["verbose"]=""

        elif opt in ("-o", "--output_type"):
            output_type = arg.upper()
            options_list["output_type"]=arg.upper()

        elif opt in ("-l", "--language"):
            lg_code = arg.upper()
            options_list["language"]=arg.upper()

        elif opt in ("-g", "--log"):
            logger = logging.getLogger('pyhpsu')
            hdlr = logging.FileHandler(arg)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.ERROR)
        options_list["cmd"]=cmd
    if verbose == "2":
        locale.setlocale(locale.LC_ALL, '')

    # config if in auto mode
    if auto:
        read_from_conf_file=True
        conf_file=default_conf_file

    # get config from file if given....
    if read_from_conf_file:
        if conf_file==None:
            print("Error, please provide a config file")
            sys.exit(9)
        else:
            try:
                with open(conf_file) as f:
                    config.readfp(f)
            except IOError:
                print("Error: config file not found")
                sys.exit(9)
        config.read(conf_file)
        if config.has_option('PYHPSU','PYHPSU_DEVICE'):
            driver=config['PYHPSU']['PYHPSU_DEVICE']
        if config.has_option('PYHPSU','PYHPSU_PORT'):
            port=config['PYHPSU']['PYHPSU_PORT']
        if config.has_option('PYHPSU','PYHPSU_LANG'):
            lg_code=config['PYHPSU']['PYHPSU_LANG']
        if config.has_option('PYHPSU','OUTPUT_TYPE'):
            output_type=config['PYHPSU']['OUTPUT_TYPE']

    else:
        conf_file=default_conf_file

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
    if output_type not in PLUGIN_LIST:
        print("Error, please specify a correct output_type [" + PLUGIN_STRING + "]")
        sys.exit(9)

    # Check Language
    if lg_code not in languages:
        print("Error, please specify a correct language [%s]" % " ".join(languages))
        sys.exit(9)
    # ------------------------------------
    # try to query different commands in different periods
    # Read them from config and group them
    #
    # create dictionary for the jobs
    if auto:
        timed_jobs=dict()
        if read_from_conf_file:                                         # if config is read from file
            if len(config.options('JOBS')):                             # if there are configured jobs
                for each_key in config.options('JOBS'):                 # for each value to query
                    job_period=config.get('JOBS',each_key)              # get the period
                    if not "timer_" + job_period in timed_jobs.keys():  # if this period isn't still in the dict
                        timed_jobs["timer_" + job_period]=[]            # create a list for this period
                    timed_jobs["timer_" + job_period].append(each_key)  # and add the value to this period
                wanted_periods=list(timed_jobs.keys())
            else:
                print("Error, please specify a value to query in config file ")
                sys.exit(9)


    #
    # Print help
    #
    if show_help:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
        if len(cmd) == 0:
            print("List available commands:")
            print("%20s - %-10s" % ('COMMAND', 'LABEL'))
            print("%20s---%-10s" % ('------------', '----------'))
            for cmd in sorted(n_hpsu.command_dict) :
                try:
                    print("%20s - %-10s" % (n_hpsu.command_dict[cmd]['name'], n_hpsu.command_dict[cmd]['label']))
                except KeyError:
                    print("""!!!!!! No translation for "%12s" !!!!!!!""" % (n_hpsu.command_dict[cmd]['name']))
        else:
            print("%12s - %-10s - %s" % ('COMMAND', 'LABEL', 'DESCRIPTION'))
            print("%12s---%-10s---%s" % ('------------', '----------', '---------------------------------------------------'))
            for c in n_hpsu.commands:
                print("%12s - %-10s - %s" % (c['name'], c['label'], c['desc']))
        sys.exit(0)

        #
        # now its time to call the hpsu and do the REAL can query
        # and handle the data as configured
        #
    if auto and not backup_mode:
        while loop:
            ticker+=1
            collected_cmds=[]
            for period_string in timed_jobs.keys():
                period=period_string.split("_")[1]
                if not ticker % int(period):
                    for job in timed_jobs[period_string]:
                        collected_cmds.append(str(job))
            if len(collected_cmds):
                n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=collected_cmds, lg_code=lg_code)
                exec('thread_%s = threading.Thread(target=read_can, args=(driver,logger,port,collected_cmds,lg_code,verbose,output_type))' % (period))
                exec('thread_%s.start()' % (period))
            time.sleep(1)
    elif backup_mode:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
        read_can(driver, logger, port, n_hpsu.backup_commands, lg_code,verbose,output_type)
    elif restore_mode:
        restore_commands=[]
        try:
            with open(backup_file, 'rU') as jsonfile:
                restore_settings=json.load(jsonfile)
                for command in restore_settings:
                    restore_commands.append(str(command["name"]) + ":" + str(command["resp"]))
                n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=restore_commands, lg_code=lg_code)
                read_can(driver, logger, port, restore_commands, lg_code,verbose,output_type)
        except FileNotFoundError:
            print("No such file or directory!!!")
            sys.exit(1)

    else:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
        read_can(driver, logger, port, cmd, lg_code,verbose,output_type)

def read_can(driver,logger,port,cmd,lg_code,verbose,output_type):
    global backup_file
    # really needed? Driver is checked above
    #if not driver:
    #    print("Error, please specify driver [ELM327 or PYCAN, EMU, HPSUD]")
    #    sys.exit(9)


    arrResponse = []

    for c in n_hpsu.commands:
            setValue = None
            for i in cmd:
                if ":" in i and c["name"] == i.split(":")[0]:
                    setValue = i.split(":")[1]
                    if not c["type"] == "value":
                        setValue = float(setValue)*float(c["divisor"])

            i = 0
            while i <= 3:
                rc = n_hpsu.sendCommand(c, setValue)
                if rc != "KO":
                    i = 4
                    if not setValue:
                        response = n_hpsu.parseCommand(cmd=c, response=rc, verbose=verbose)
                        resp = n_hpsu.umConversion(cmd=c, response=response, verbose=verbose)

                        arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"]})
                else:
                    i += 1
                    time.sleep(2.0)
                    n_hpsu.printd('warning', 'retry %s command %s' % (i, c["name"]))
                    if i == 4:
                        n_hpsu.printd('error', 'command %s failed' % (c["name"]))

    if output_type == "JSON":
        if len(arrResponse)!=0:
            print(arrResponse)
    elif output_type == "CSV":
        for r in arrResponse:
            print("%s,%s,%s" % (r["timestamp"], r["name"], r["resp"]))
    elif output_type == "BACKUP":
        print("Writing Backup to " + str(backup_file)) 
        try:
            with open(backup_file, 'w') as outfile:
                json.dump(arrResponse, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
        except FileNotFoundError:
            print("No such file or directory!!!")
            sys.exit(1)
        

    else:
        module_name=output_type.lower()
        module = importlib.import_module("HPSU.plugins." + module_name)
        hpsu_plugin = module.export(hpsu=n_hpsu, logger=logger, config_file=conf_file)
        hpsu_plugin.pushValues(vars=arrResponse)


    

if __name__ == "__main__":
    main(sys.argv[1:])
