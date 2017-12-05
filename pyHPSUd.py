#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# v 0.0.4 by Vanni Brutto (Zanac)
# DONT use CTRL+C to Terminate, else Port is blocked

import pika
#import threading
import serial
import time
import sys
sys.path.append('/usr/share/pyHPSU/HPSU/');
import getopt
import logging
import json
   
from HPSU.HPSU import HPSU


#-------------------------------------------------------------------
DEBUG = True
DEBUG = False
verbose = "1"
logger = None
#-------------------------------------------------------------------

try:
    DEBUG
except NameError:
    DEBUG = False

if DEBUG:
    print("Enabling DEBUG mode!")

def printD(message):
    if DEBUG:
        print(message)
        sys.stdout.flush()


class MainHPSU(object):
    def main2(self, argv):
        cmd = []
        driver = None
        verbose = "1"
        help = False
        port = None
        lg_code = None
        languages = ["EN", "IT", "DE"]        

        try:
            opts, args = getopt.getopt(argv,"hp:d:v:l:g:", ["help", "port=", "driver=", "verbose=", "language=", "log="])
        except getopt.GetoptError:
            print('pyHPSUd.py -d DRIVER')
            print(' ')
            print('           -d  --driver           driver name: [ELM327, PYCAN, EMU]')
            print('           -p  --port             port (eg COM or /dev/tty*, only for ELM327 driver)')
            print('           -v  --verbose          verbosity: [1, 2]   default 1')
            print('           -l  --language         set the language to use [%s]' % " ".join(languages) )
            print('           -g  --log              set the log to file [_filename]')
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                help = True
            elif opt in ("-d", "--driver"):
                driver = arg.upper()
            elif opt in ("-p", "--port"):
                port = arg
            elif opt in ("-v", "--verbose"):
                verbose = arg
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
                logger.setLevel(logging.WARNING)

        self.hpsu = HPSU(driver=driver, logger=None, port=port, cmd=cmd, lg_code=lg_code)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()

        channel.queue_delete(queue='hpsu_queue')
        channel.queue_declare(queue='hpsu_queue', arguments={"x-max-priority":3})
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(self.on_request, queue='hpsu_queue')
        channel.start_consuming()

    def on_request(self, ch, method, props, body):
        message = json.loads(body.decode('UTF-8'))
        name = message["name"]
        value = message["value"]
        type = message["type"]
        sec = 0
        time.sleep(sec)
        
        rc = "KO"
        print ("1")
        for cmd in self.hpsu.commands:
            print ("1.5")
            if name == cmd["name"]:
                print(str(cmd))
                print(name)
                print("set:%s:" % value)
                rc = self.hpsu.sendCommand(cmd, value)
                print ("1.7")
        print ("2")
        
        if type == "sync":
            priority = 2
            response = rc
            print(rc)
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(priority=priority, correlation_id = props.correlation_id),
                             body=str(response))
            print("spedito"+props.reply_to)
        ch.basic_ack(delivery_tag = method.delivery_tag)    

    
def _exit():
    try:
        read_thread.exit()
        socket_server_thread.exit()
        sys.exit()
    except (Exception, e3):
        exit()
    
if __name__ == '__main__':
    #main(sys.argv[1:])
    main = MainHPSU()
    main.main2(sys.argv[1:])

