#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# v 0.0.4 by Vanni Brutto (Zanac)
# DONT use CTRL+C to Terminate, else Port is blocked

import threading
import serial
import time
import sys
import socket
import getopt
import logging
try:
    import SocketServer as socketserver
except ImportError:
    import socketserver
from HPSU.HPSU import HPSU


#-------------------------------------------------------------------
mutex = threading.Lock()
DEBUG = True
DEBUG = False
SocketHost = "0.0.0.0"
SocketPort = 7060
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


#parse Socket request
def ParseSocketRequest(cmdName, hpsu):
    cmdName = cmdName.decode('UTF-8')
    for cmd in hpsu.commands:
        if cmdName == cmd["name"]:            
            sec = 0
            """if cmdName == "qsc":
                sec = 10
            if cmdName == "qch":
                sec = 1"""
            time.sleep(sec)
            mutex.acquire()
            rc = hpsu.sendCommand(cmd)
            if (rc != "KO"):
                mutex.release()
                return rc
            else:
                mutex.release()
                return rc

    returnlist = "Command %s not available\n" % cmdName
    return returnlist

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        printD("SocketRequest: {}".format(self.data))
        try:
            resp = ParseSocketRequest(self.data, self.server.hpsu)
            self.wfile.write(resp.encode())
        except (Exception, e2):
            print("Error in ThreadedTCPRequestHandler: " + str(e2))
        except (KeyboardInterrupt, SystemExit):
            _exit()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def main(argv):
    cmd = []
    port = None
    driver = None
    verbose = "1"
    help = False
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

    hpsu = HPSU(driver=driver, logger=None, port=port, cmd=cmd, lg_code=lg_code)
    HOST, PORT = SocketHost, SocketPort
    socket_server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    socket_server.hpsu = hpsu
    ip, port = socket_server.server_address
    
    # Start a thread with the server - that thread will then start one more thread for each request
    socket_server_thread = threading.Thread(target=socket_server.serve_forever)
    socket_server_thread.start()
    print("pyHPSUd started.")

def _exit():
    try:
        read_thread.exit()
        socket_server_thread.exit()
        sys.exit()
    except (Exception, e3):
        exit()
    
if __name__ == '__main__':
    main(sys.argv[1:])

