#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-

# config inf conf_file for MQTT Daemon mode (defaults):
# [MQTT]
# BROKER = localhost
# PORT = 1883
# USERNAME = 
# PASSWORD = 
# CLIENTNAME = rotex_hpsu
# PREFIX = rotex
# COMMANDTOPIC = command
# STATUSTOPIC = status

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
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt

SocketPort = 7060
logger = None
n_hpsu = None
driver = None
port = None
lg_code = None
verbose = None
output_type = None
mqtt_client = None
mqtt_prefix = None
mqttdaemon_command_topic = "command"
mqttdaemon_status_topic = "status"


def main(argv):
    global logger
    global n_hpsu
    global driver
    global port
    global lg_code
    global verbose
    global output_type
    global mqtt_client
    global mqtt_prefix
    global mqttdaemon_command_topic
    global mqttdaemon_status_topic

    cmd = []
    port = None
    driver = "PYCAN"
    verbose = "1"
    show_help = False
    # empty list, if none is specified with options and configuration, JSON default will be used
    output_type = []
    upload = False
    lg_code = "EN"
    languages = ["EN", "IT", "DE"]
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
    LOG_LEVEL_STRING = 'DEBUG, INFO, WARNING, ERROR, CRITICAL'
    # default to loggin.error if --log_level option not present
    desired_log_level = logging.ERROR
    # default log to stdout if no file specified
    log_handler = logging.StreamHandler()
    # default log formatter
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #commands = []
    #listCommands = []
    global config
    config = configparser.ConfigParser()
    env_encoding=sys.stdout.encoding
    PLUGIN_PATH="/usr/lib/python3/dist-packages/HPSU/plugins"
    backup_mode=False
    global backup_file
    restore_mode=False
    global options_list
    options_list={}
    mqttdaemon_option_present = False
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
        opts, args = getopt.getopt(argv,"ahc:p:d:v:o:l:g:f:b:r:", ["help", "cmd=", "port=", "driver=", "verbose=", "output_type=", "upload=", "language=", "log=", "log_level=", "config_file=", "mqtt_daemon"])
    except getopt.GetoptError:
        print('pyHPSU.py -d DRIVER -c COMMAND')
        print(' ')
        print('           -a  --auto            do automatic queries')
        print('           -f  --config          Configfile, overrides given commandline arguments')
        print('           -d  --driver          driver name: [ELM327, PYCAN, EMU, HPSUD], Default: PYCAN')
        print('           -p  --port            port (eg COM or /dev/tty*, only for ELM327 driver)')
        print('           -o  --output_type     output type: [' + PLUGIN_STRING + '] default JSON')
        print('           -c  --cmd             command: [see commands domain]')
        print('           -v  --verbose         verbosity: [1, 2]   default 1')
        print('           -l  --language        set the language to use [%s], default is \"EN\" ' % " ".join(languages))
        print('           -b  --backup          backup configurable settings to file [filename]')
        print('           -r  --restore         restore HPSU settings from file [filename]')
        print('           --mqtt_daemon         set up an mqtt daemon that subscribe to a command topic and executes received command on HPSU')
        print('           -g  --log             set the log to file [filename]')
        print('           --log_level           set the log level to [' + LOG_LEVEL_STRING + ']')
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
            output_type.append("BACKUP")
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
            if arg.upper() not in output_type:
                output_type.append(arg.upper())
            if not "output_type" in options_list or options_list["output_type"] is None or options_list["output_type"]=="":
                options_list["output_type"]=arg.upper()
            else:
                options_list["output_type"]+=", " + arg.upper()

        elif opt in ("-l", "--language"):
            lg_code = arg.upper()
            options_list["language"]=arg.upper()

        elif opt in ("--mqtt_daemon"):
            mqttdaemon_option_present = True

        elif opt in ("-g", "--log"):
            log_handler = logging.FileHandler(arg)
            options_list["log_file"]=arg

        elif opt in ("--log_level"):
            if arg == 'DEBUG':
                desired_log_level = logging.DEBUG
            elif arg == 'INFO':
                desired_log_level = logging.INFO
            elif arg == 'WARNING':
                desired_log_level = logging.WARNING
            elif arg == 'ERROR':
                desired_log_level = logging.ERROR
            elif arg == 'CRITICAL':
                desired_log_level = logging.CRITICAL
            else:
                print("Error, " + arg + " is not a valid value for log_level option, use [" + LOG_LEVEL_STRING + "]")
                sys.exit(2)
        options_list["cmd"]=cmd
        
    # if no log file has been specified and driver is HPSUD then log nothing
    if options_list.get("log_file") is None and driver == "HPSUD":
        log_handler = logging.NullHandler

    logger = logging.getLogger('pyhpsu')
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    logger.setLevel(desired_log_level)

    if verbose == "2":
        locale.setlocale(locale.LC_ALL, '')

    # if no config file option is present...
    if not read_from_conf_file:
        # ...set the default one...
        # NOTE: other modules may need to load it later
        conf_file=default_conf_file
        # ...but auto or mqttdaemon mode needs it loaded...
        if auto or mqttdaemon_option_present:
            # ...read it
            read_from_conf_file=True

    # get config from file if given....
    if read_from_conf_file:
        if conf_file==None:
            logger.critical("please provide a config file")
            sys.exit(9)
        else:
            try:
                with open(conf_file) as f:
                    config.read_file(f)
            except IOError:
                logger.critical("config file not found")
                sys.exit(9)
        config.read(conf_file)
        if driver=="" and config.has_option('PYHPSU','PYHPSU_DEVICE'):
            driver=config['PYHPSU']['PYHPSU_DEVICE']
        if port=="" and config.has_option('PYHPSU','PYHPSU_PORT'):
            port=config['PYHPSU']['PYHPSU_PORT']
        if lg_code=="" and config.has_option('PYHPSU','PYHPSU_LANG'):
            lg_code=config['PYHPSU']['PYHPSU_LANG']
        if len(output_type)==0 and config.has_option('PYHPSU','OUTPUT_TYPE'):
            output_type.append(config['PYHPSU']['OUTPUT_TYPE'])

        if config.has_option('MQTT', 'BROKER'):
            mqtt_brokerhost = config['MQTT']['BROKER']
        else:
            mqtt_brokerhost = 'localhost'

        if config.has_option('MQTT', 'PORT'):
            mqtt_brokerport = int(config['MQTT']['PORT'])
        else:
            mqtt_brokerport = 1883

        if config.has_option('MQTT', 'CLIENTNAME'):
            mqtt_clientname = config['MQTT']['CLIENTNAME']
        else:
            mqtt_clientname = 'rotex'

        if config.has_option('MQTT', 'USERNAME'):
            mqtt_username = config['MQTT']['USERNAME']
        else:
            mqtt_username = None
            logger.error("Username not set!!!!!")

        if config.has_option('MQTT', "PASSWORD"):
            mqtt_password = config['MQTT']['PASSWORD']
        else:
            mqtt_password="None"

        if config.has_option('MQTT', "PREFIX"):
            mqtt_prefix = config['MQTT']['PREFIX']
        else:
            mqtt_prefix = ""

        #MQTT MQTT Daemon command topic
        if config.has_option('MQTT', "COMMAND"):
            mqttdaemon_command_topic = config['MQTT']['COMMAND']
# default already set
#        else:
#            mqttdaemon_command_topic = ""

        #MQTT MQTT Daemon status topic
        # FIXME to be used for pyHPSU status, including MQTTDAEMON mode, not for actual parameter reading
        if config.has_option('MQTT', "STATUS"):
            mqttdaemon_status_topic = config['MQTT']['STATUS']
# default already set
#        else:
#            mqttdaemon_status_topic = ""

        if config.has_option('MQTT', "QOS"):
            mqtt_qos = config['MQTT']['QOS']
        else:
            mqtt_qos = "0"

        if config.has_option('MQTT', "RETAIN"):
            mqtt_retain = config['MQTT']['RETAIN']
        else:
            mqtt_retain = "False"

        logger.info("configuration parsing complete")   

    # default output_type if not specified
    if len(output_type)==0:
        output_type.append("JSON")

    #
    # now we should have all options...let's check them
    #
    # Check driver
    if driver not in ["ELM327", "PYCAN", "EMU", "HPSUD"]:
        logger.critical("please specify a correct driver [ELM327, PYCAN, EMU, HPSUD] ")
        sys.exit(9)

    if driver == "ELM327" and port == "":
        logger.critical("please specify a correct port for the ELM327 device ")
        sys.exit(9)

    # Check output type
    for plugin in output_type:
        if plugin not in PLUGIN_LIST:
            logger.critical("please specify a correct output_type [" + PLUGIN_STRING + "], " + plugin + " does not exist")
            sys.exit(9)

    # Check Language
    if lg_code not in languages:
        logger.critical("please specify a correct language [%s]" % " ".join(languages))
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
                logger.critical("please specify a value to query in config file ")
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
                    print("%20s - %-10s" % (n_hpsu.command_dict[cmd]['name'], (n_hpsu.command_dict[cmd]['label']) + ('' if n_hpsu.command_dict[cmd]['writable']=='true' else ' (readonly)')))
                except KeyError:
                    error_message = """!!!!!! No translation for "%12s" !!!!!!!""" % (n_hpsu.command_dict[cmd]['name'])
                    print(error_message)
                    logger.error(error_message)
        else:
            print("%12s - %-10s - %s" % ('COMMAND', 'LABEL', 'DESCRIPTION'))
            print("%12s---%-10s---%s" % ('------------', '----------', '---------------------------------------------------'))
            for c in n_hpsu.commands:
                print("%12s - %-10s - %s" % (c['name'], c['label'] + ('' if c['writable']=='true' else ' (readonly)'), c['desc']))
        sys.exit(0)

        #
        # now its time to call the hpsu and do the REAL can query
        # and handle the data as configured
        #
    if mqttdaemon_option_present:
        logger.info("creating new mqtt client instance: " + mqtt_clientname)
        mqtt_client = mqtt.Client(mqtt_clientname)
        if mqtt_username:
            mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
            mqtt_client.enable_logger()

        mqtt_client.on_message=on_mqtt_message
        logger.info("connecting to broker: " + mqtt_brokerhost)
        mqtt_client.connect(mqtt_brokerhost)

        command_topic = mqtt_prefix + "/" + mqttdaemon_command_topic + "/+"
        logger.info("Subscribing to command topic: " + command_topic)
        mqtt_client.subscribe(command_topic)

        # this blocks execution
        #mqtt_client.loop_forever()
        mqtt_client.loop_start()

    if backup_mode:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
        read_can(driver, logger, port, n_hpsu.backup_commands, lg_code,verbose,output_type)
    elif auto:
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
            logger.error("No such file or directory!!!")
            sys.exit(1)

    else:
        n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=cmd, lg_code=lg_code)
        read_can(driver, logger, port, cmd, lg_code,verbose,output_type)

def read_can(driver,logger,port,cmd,lg_code,verbose,output_type):
    global backup_file
    global mqtt_prefix
    global mqttdaemon_status_topic
    global mqtt_client

    # really needed? Driver is checked above
    #if not driver:
    #    logger.critical("Error, please specify driver [ELM327 or PYCAN, EMU, HPSUD]")
    #    sys.exit(9)

    arrResponse = []

    for c in n_hpsu.commands:
            setValue = None
            for i in cmd:
                if ":" in i and c["name"] == i.split(":")[0]:
                    setValue = i.split(":")[1]
                    if c["writable"] != "true":
                        logger.critical(c["name"] + " is a readonly command")
                        sys.exit(9)
                    if not c["type"] == "value":
                        setValue = float(setValue)*float(c["divisor"])
                    else:
                        logger.error('type "value" not implemented since yet')
                        return

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
                    logger.warning('retry %s command %s' % (i, c["name"]))
                    if i == 4:
                        logger.error('command %s failed' % (c["name"]))

    for output_type_name in output_type: 
        if output_type_name == "JSON":
            if len(arrResponse)!=0:
                print(arrResponse)
        elif output_type_name == "CSV":
            for r in arrResponse:
                print("%s,%s,%s" % (r["timestamp"], r["name"], r["resp"]))
        elif output_type_name == "BACKUP":
            error_message = "Writing Backup to " + str(backup_file)
            print(error_message)
            logger.info(error_message)
            
            try:
                with open(backup_file, 'w') as outfile:
                    json.dump(arrResponse, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
            except FileNotFoundError:
                error_message = "No such file or directory!!!"
                print(error_message)
                logger.error(error_message)
                sys.exit(1)
        elif output_type_name == "MQTTDAEMON":
            for r in arrResponse:
                # retain=False to conform to usual mqtt plugin output
                mqtt_client.publish(mqtt_prefix + "/" + r["name"], r["resp"], qos=0, retain=False)
                # variant with timestamp and on "status" topic, not conforming with usual mqtt plugin output
                #mqtt_client.publish(mqtt_prefix + "/" + mqttdaemon_status_topic + "/" + r["name"], "{'name': '%s', 'resp': '%s', 'timestamp': %s}" % (r["name"], r["resp"], r["timestamp"]), qos=0, retain=True)

        else:
            module_name=output_type_name.lower()
            module = importlib.import_module("HPSU.plugins." + module_name)
            hpsu_plugin = module.export(hpsu=n_hpsu, logger=logger, config_file=conf_file)
            hpsu_plugin.pushValues(vars=arrResponse)

def on_disconnect(client, userdata,rc=0):
    logger.debug("mqtt disConnected: result code " + str(rc))
    client.loop_stop()
    
def on_mqtt_message(client, userdata, message):
    global logger
    global driver
    global port
    global lg_code
    global verbose
    global output_type
    global n_hpsu

    logger.debug("complete topic: " + message.topic)
    mqtt_command = message.topic.split('/')[-1]
    logger.debug("command topic: " + mqtt_command)
    mqtt_value = str(message.payload.decode("utf-8"))
    logger.debug("value: " + mqtt_value)
    if mqtt_value == '' or mqtt_value == None or mqtt_value == "read":
        hpsu_command_string = mqtt_command
    else:
        hpsu_command_string = mqtt_command + ":" + mqtt_value
    hpsu_command_list = [hpsu_command_string]
    logger.info("setup HPSU to accept commands")
    n_hpsu = HPSU(driver=driver, logger=logger, port=port, cmd=hpsu_command_list, lg_code=lg_code)
    logger.info("send command to hpsu: " + hpsu_command_string)
    #exec('thread_mqttdaemon = threading.Thread(target=read_can(driver, logger, port, hpsu_command_list, lg_code,verbose,["MQTTDAEMON"]))')
    #exec('thread_mqttdaemon.start()')
    read_can(driver, logger, port, hpsu_command_list, lg_code,verbose,["MQTTDAEMON"])
    # if command was a write, re-read the value from HPSU and publish to MQTT
    if ":" in hpsu_command_string:
        hpsu_command_string_reread_after_write = hpsu_command_string.split(":")[0]
        hpsu_command_string_reread_after_write_list = [hpsu_command_string_reread_after_write]
        #exec('thread_mqttdaemon_reread = threading.Thread(target=read_can(driver, logger, port, hpsu_command_string_reread_after_write_list, lg_code,verbose,["MQTTDAEMON"]))')
        #exec('thread_mqttdaemon_reread.start()')
        read_can(driver, logger, port, hpsu_command_string_reread_after_write_list, lg_code,verbose,["MQTTDAEMON"])
 
if __name__ == "__main__":
    main(sys.argv[1:])
