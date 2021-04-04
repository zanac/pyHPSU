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
# STATUSTOPIC = status ...for future use
# QOS = 0
# ADDTIMESTAMP = False ...whether or not to add timestamp to published values

import serial
import sys
import traceback
#sys.path.append('/usr/share/pyHPSU/HPSU')
#sys.path.append('/usr/share/pyHPSU/plugins')
import os
import time
import locale
import uuid
import importlib
import logging
from HPSU.HPSU import HPSU
import argparse
import configparser
import threading
import json
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
import paho.mqtt.client as mqtt

logger = None
n_hpsu = None
# global options object
options = None
mqtt_client = None
mqtt_prefix = None
mqtt_qos = 0
mqtt_retain = False
mqtt_addtimestamp = False
mqttdaemon_command_topic = "command"
mqttdaemon_status_topic = "status"
# unique randomized value per program execution that can be used where needed
execution_uuid = str(uuid.uuid4())[:8]

def my_except_hook(exctype, value, traceback):
    if exctype == KeyboardInterrupt:
        print("Interrupted by user")
    else:
        sys.__excepthook__(exctype, value, traceback)

def main(argv):
    global options
    global logger
    global n_hpsu
    global mqtt_client
    global mqtt_prefix
    global mqtt_qos
    global mqtt_retain
    global mqtt_addtimestamp
    global mqttdaemon_command_topic
    global mqttdaemon_status_topic

    sys.excepthook = my_except_hook
    cmd = None
    languages = ["EN", "IT", "DE"]
    global default_conf_file
    default_conf_file = "/etc/pyHPSU/pyhpsu.conf"
    read_from_conf_file=False
    global ticker
    ticker=0
    loop=True
    LOG_LEVEL_LIST = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    # default log formatter
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    #commands = []
    #listCommands = []
    global config
    config = configparser.ConfigParser()
    PLUGIN_PATH="/usr/lib/python3/dist-packages/HPSU/plugins"
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

    parser = argparse.ArgumentParser(description="pyHPSU is a set of python scripts and other files to read and modify the values\nof the Rotex® HPSU (possibly) also identical heating pumps from Daikin®).",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="- If no command is specified, all commands in dictionary are executed\n- To set a value use <command>:<value>")
    parser.add_argument("--dictionary", action="store_true", dest="show_help", help="show complete command dictionary or specific command help")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0-BETA1')
    parser.add_argument("-a", "--auto", action="store_true", help="do automatic queries")
    parser.add_argument("-f", "--config", dest="conf_file", help="Configfile, overrides given commandline arguments")
    backup_restore_group = parser.add_mutually_exclusive_group()
    backup_restore_group.add_argument("-b", "--backup", dest="backup_file", help="backup configurable settings to file [filename]")
    backup_restore_group.add_argument("-r", "--restore", dest="restore_file", help="restore HPSU settings from file [filename]")
    parser.add_argument("-g", "--log", dest="log_file", help="set the log to file [filename]")
    parser.add_argument("--log_level", choices=LOG_LEVEL_LIST, type=str.upper, default="ERROR", help="set the log level to [" + ", ".join(LOG_LEVEL_LIST) + "]")
    parser.add_argument("-l", "--language", dest="lg_code", choices=languages, type=str.upper, default="EN", help="set the language to use [%s], default is \"EN\" " % " ".join(languages))
    parser.add_argument("-d", "--driver", type=str.upper, default="PYCAN", help="driver name: [ELM327, PYCAN, EMU, HPSUD], Default: PYCAN")
    parser.add_argument("-c", "--cmd", action="append", help="command: [see commands dictionary]")
    parser.add_argument("-o", "--output_type", action="append", type=str.upper, choices=PLUGIN_LIST, help="output type: [" + ", ".join(PLUGIN_LIST) + "] default JSON")
    parser.add_argument("-v", "--verbose", default="1", help="verbosity: [1, 2] default 1")
    parser.add_argument("-p", "--port", help="port (eg COM or /dev/tty*, only for ELM327 driver)")
    parser.add_argument("--mqtt_daemon", action="store_true", help="set up an mqtt daemon that subscribe to a command topic and executes received command on HPSU")

    try:
        options = parser.parse_args()
    except IOError as e:
        parser.error(e)
    if (options == None):
        print(parser.usage)
        exit(0)
    else:
        # set the default value if no output_type is chosen (not possible with add_argument() because it does
        # not detect duplication e.g. when JSON is also chosen)
        if options.output_type is None:
            options.output_type = ["JSON"]
        cmd = [] if options.cmd is None else options.cmd
        if options.backup_file is not None:
            options.output_type.append("BACKUP")
        read_from_conf_file = options.conf_file is not None
        # if no log file has been specified and driver is HPSUD then log nothing
        if options.log_file is None and options.driver == "HPSUD":
            _log_handler = logging.NullHandler
        elif options.log_file is not None:
            _log_handler = logging.FileHandler(options.log_file)
        else:
            # default log to stdout if no file specified
            _log_handler = logging.StreamHandler()


    logger = logging.getLogger('pyhpsu')
    _log_handler.setFormatter(log_formatter)
    logger.addHandler(_log_handler)
    logger.setLevel(options.log_level)

    if options.verbose == "2":
        locale.setlocale(locale.LC_ALL, '')

    # if no config file option is present...
    if not read_from_conf_file:
        # ...set the default one...
        # NOTE: other modules may need to load it later
        options.conf_file=default_conf_file
        # ...but auto or mqttdaemon mode needs it loaded...
        if options.auto or options.mqtt_daemon:
            # ...read it
            read_from_conf_file=True

    # get config from file if given....
    if read_from_conf_file:
        try:
            with open(options.conf_file) as f:
                config.read_file(f)
        except IOError:
            logger.critical("config file not found")
            sys.exit(9)
        config.read(options.conf_file)
        if options.driver=="" and config.has_option('PYHPSU','PYHPSU_DEVICE'):
            options.driver=config['PYHPSU']['PYHPSU_DEVICE']
        if options.port=="" and config.has_option('PYHPSU','PYHPSU_PORT'):
            options.port=config['PYHPSU']['PYHPSU_PORT']
        if options.lg_code=="" and config.has_option('PYHPSU','PYHPSU_LANG'):
            options.lg_code=config['PYHPSU']['PYHPSU_LANG'].upper()
        if len(options.output_type)==0 and config.has_option('PYHPSU','OUTPUT_TYPE'):
            options.output_type.append(config['PYHPSU']['OUTPUT_TYPE'])

        # object to store entire MQTT config section
        mqtt_config = config['MQTT']
        # MQTT Daemon command topic
        mqttdaemon_command_topic = mqtt_config.get('COMMAND', 'command')
        # MQTT Daemon status topic
        # FIXME to be used for pyHPSU status, including MQTTDAEMON mode, not for actual parameter reading
        mqttdaemon_status_topic = mqtt_config.get('STATUS', 'status')
        mqtt_brokerhost = mqtt_config.get('BROKER', 'localhost')
        mqtt_brokerport = mqtt_config.getint('PORT', 1883)
        mqtt_clientname = mqtt_config.get('CLIENTNAME', 'rotex')
        mqtt_username = mqtt_config.get('USERNAME', None)
        if mqtt_username is None:
            logger.error("Username not set!!!!!")
        mqtt_password = mqtt_config.get('PASSWORD', "NoPasswordSpecified")
        mqtt_prefix = mqtt_config.get('PREFIX', "")
        mqtt_qos = mqtt_config.getint('QOS', 0)
        # every other value implies false
        mqtt_retain = mqtt_config.get('RETAIN', "NOT TRUE") == "True"
        # every other value implies false
        mqtt_addtimestamp = mqtt_config.get('ADDTIMESTAMP', "NOT TRUE") == "True"

        logger.info("configuration parsing complete")   

    #
    # now we should have all options...let's check them
    #
    if options.driver == "ELM327" and options.port == "":
        logger.critical("please specify a correct port for the ELM327 device ")
        sys.exit(9)

    # ------------------------------------
    # try to query different commands in different periods
    # Read them from config and group them
    #
    # create dictionary for the jobs
    if options.auto:
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
    if options.show_help:
        n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=cmd, lg_code=options.lg_code)
        if len(cmd) == 0:
            print("List available commands:")
            print("%20s - %-10s" % ('COMMAND', 'LABEL'))
            print("%20s---%-10s" % ('------------', '----------'))
            for cmd in sorted(n_hpsu.command_dict) :
                if 'label' in n_hpsu.command_dict[cmd]:
                    print("%20s - %-10s" % (n_hpsu.command_dict[cmd]['name'], (n_hpsu.command_dict[cmd]['label']) + ('' if n_hpsu.command_dict[cmd]['writable']=='true' else ' (readonly)')))
                else:
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
    if options.mqtt_daemon:
        _mqttdaemon_clientname = mqtt_clientname + "-mqttdaemon-" + execution_uuid
        logger.info("creating new mqtt client instance: " + _mqttdaemon_clientname)
        # a different client name because otherwise mqtt output plugin closes this connection, too
        mqtt_client = mqtt.Client(_mqttdaemon_clientname)
        if mqtt_username:
            mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
            mqtt_client.enable_logger()

        mqtt_client.on_message=on_mqtt_message
        logger.info("connecting to broker: " + mqtt_brokerhost + ", port: " + str(mqtt_brokerport))
        mqtt_client.connect(mqtt_brokerhost, mqtt_brokerport)

        command_topic = mqtt_prefix + "/" + mqttdaemon_command_topic + "/+"
        logger.info("Subscribing to command topic: " + command_topic)
        mqtt_client.subscribe(command_topic)

        # this blocks execution
        #mqtt_client.loop_forever()
        if options.auto:
            mqtt_client.loop_start()

    # if a backup file is specified we are in backup mode
    if options.backup_file is not None:
        n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=cmd, lg_code=options.lg_code)
        read_can(n_hpsu.backup_commands, options.verbose, options.output_type)
    elif options.auto:
        while loop:
            ticker+=1
            collected_cmds=[]
            for period_string in timed_jobs.keys():
                period=period_string.split("_")[1]
                if not ticker % int(period):
                    for job in timed_jobs[period_string]:
                        collected_cmds.append(str(job))
            if len(collected_cmds):
                n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=collected_cmds, lg_code=options.lg_code)
                exec('thread_%s = threading.Thread(target=read_can, args=(collected_cmds,options.verbose,options.output_type))' % (period))
                exec('thread_%s.start()' % (period))
            time.sleep(1)
    # if a restore file is specified we are in restore mode
    elif options.restore_file is not None:
        restore_commands=[]
        try:
            with open(options.restore_file, 'rU') as jsonfile:
                restore_settings=json.load(jsonfile)
                for command in restore_settings:
                    restore_commands.append(str(command["name"]) + ":" + str(command["resp"]))
                n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=restore_commands, lg_code=options.lg_code)
                read_can(restore_commands, options.verbose, options.output_type)
        except FileNotFoundError:
            logger.error("No such file or directory!!!")
            sys.exit(1)

    # FIXME if no command is specified and mqttdaemon mode is active, don't query all the commands (this has to be discussed)
    elif not (len(cmd)==0 and options.mqtt_daemon):
        n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=cmd, lg_code=options.lg_code)
        read_can(cmd, options.verbose, options.output_type)

    # if we reach this point (the end), we are not in auto mode so the loop is not started
    if mqtt_client is not None:
        mqtt_client.loop_forever()


def read_can(cmd, verbose, output_type):
    global options
    global logger
    global mqtt_prefix
    global mqttdaemon_status_topic
    global mqtt_client

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
                        if not setValue.isdigit():
                            key=str(setValue)
                            setValue=c["value_code"][key]

            i = 0
            while i <= 3:
                rc = n_hpsu.sendCommand(c, setValue)
                if rc != "KO":
                    i = 4
                    if not setValue:
                        response = n_hpsu.parseCommand(cmd=c, response=rc, verbose=options.verbose)
                        resp = n_hpsu.umConversion(cmd=c, response=response, verbose=options.verbose)

                        if "value_code" in c:
                            # FIXME special treatment is needed for commands sharing the same byte 'ouside_conf' and 'storage' conf
                            #       while not fixed a warning is raised
                            # e.g. HPSU returns a value of 26628 for both of them and the two values have to be extracted from
                            #      different part of the number
                            if resp in dict(map(reversed, c["value_code"].items())):
                                _resp_description = dict(map(reversed, c["value_code"].items()))[resp]
                            else:
                                _resp_description = 'unable to decode value ' + resp
                                logger.warning("command \"" + c["name"] + "\" " + _resp_description)
                            arrResponse.append({"name":c["name"], "resp":resp, "timestamp":response["timestamp"], "desc":_resp_description})
                        else:
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
            error_message = "Writing Backup to " + str(options.backup_file)
            print(error_message)
            logger.info(error_message)
            
            try:
                with open(options.backup_file, 'w') as outfile:
                    json.dump(arrResponse, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
            except FileNotFoundError:
                error_message = "No such file or directory!!!"
                print(error_message)
                logger.error(error_message)
                sys.exit(1)
        elif output_type_name == "MQTTDAEMON":
            for r in arrResponse:
                if mqtt_addtimestamp:
                    # use the same format as JSON output
                    # with timestamp included, retain=true become more interesting
                    if "desc" in r:
                        mqtt_client.publish(mqtt_prefix + "/" + r["name"], "{'name': '%s', 'resp': '%s', 'timestamp': %s, 'desc': '%s'}" % (r["name"], r["resp"], r["timestamp"], r["desc"]), qos=mqtt_qos, retain=mqtt_retain)
                    else:
                        mqtt_client.publish(mqtt_prefix + "/" + r["name"], "{'name': '%s', 'resp': '%s', 'timestamp': %s}" % (r["name"], r["resp"], r["timestamp"]), qos=mqtt_qos, retain=mqtt_retain)
                else:
                    mqtt_client.publish(mqtt_prefix + "/" + r["name"], r["resp"], qos=mqtt_qos, retain=mqtt_retain)

        else:
            module_name=output_type_name.lower()
            module = importlib.import_module("HPSU.plugins." + module_name)
            hpsu_plugin = module.export(hpsu=n_hpsu, logger=logger, config_file=options.conf_file)
            hpsu_plugin.pushValues(vars=arrResponse)

def on_disconnect(client, userdata, rc=0):
    logger.debug("mqtt disConnected: result code " + str(rc))
    client.loop_stop()
    
def on_mqtt_message(client, userdata, message):
    global options
    global logger
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
    n_hpsu = HPSU(driver=options.driver, logger=logger, port=options.port, cmd=hpsu_command_list, lg_code=options.lg_code)
    logger.info("send command to hpsu: " + hpsu_command_string)
    #exec('thread_mqttdaemon = threading.Thread(target=read_can(hpsu_command_list, options.verbose, ["MQTTDAEMON"]))')
    #exec('thread_mqttdaemon.start()')
    read_can(hpsu_command_list, options.verbose, ["MQTTDAEMON"])
    # if command was a write, re-read the value from HPSU and publish to MQTT
    if ":" in hpsu_command_string:
        hpsu_command_string_reread_after_write = hpsu_command_string.split(":")[0]
        hpsu_command_string_reread_after_write_list = [hpsu_command_string_reread_after_write]
        #exec('thread_mqttdaemon_reread = threading.Thread(target=read_can(hpsu_command_string_reread_after_write_list, options.verbose, ["MQTTDAEMON"]))')
        #exec('thread_mqttdaemon_reread.start()')
        logger.info("send same command in read mode to hpsu: " + hpsu_command_string)
        read_can(hpsu_command_string_reread_after_write_list, options.verbose, ["MQTTDAEMON"])
    # restarts the loop
    if options.auto:
        mqtt_client.loop_start()

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:
        # print complete information
        traceback.print_exc()
        #print("Exception: {}".format(type(e).__name__))
        #print("Exception message: {}".format(e))