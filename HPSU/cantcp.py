#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)

import sys
import socket
import time
import pika
import uuid
import json

SocketPort = 7060

class CanTCP(object):
    sock = None
    hpsu = None
    
    def __init__(self, hpsu=None):
        self.hpsu = hpsu
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True, arguments={"x-max-priority":5})
        self.callback_queue = result.method.queue

        #if type == "sync":
        self.channel.basic_consume(self.on_response, no_ack=True, 
                                   queue=self.callback_queue)
        
    def on_response(self, ch, method, props, body):
        """print(body)
        print ("confronto")
        print(str(self.corr_id))
        print(str(props.correlation_id))"""

        if self.corr_id == props.correlation_id:
            self.response = body
            #print("uguale")

    def initInterface(self):
        pass        
    
    def sendCommandWithID(self, cmd, setValue=None, priority=1):    
        if setValue:
            priority = 3
            self.response = None
            self.corr_id = str(uuid.uuid4())
            #print("spedisco:"+str(self.corr_id))
            dataSEND = {"name":cmd["name"], "value":setValue, "type":"sync"}
            self.channel.basic_publish(exchange='',
                                       routing_key='hpsu_queue',
                                       properties=pika.BasicProperties(
                                             reply_to = self.callback_queue,
                                             priority=priority,
                                             correlation_id = self.corr_id,
                                             ),
                                       body=str(json.dumps(dataSEND)))
            timeout = 0
            while self.response is None and timeout <= 200:
                time.sleep(0.1)
                self.connection.process_data_events()
                timeout += 1
            #print(str(timeout))
            if timeout >= 200:
                self.response = b"KO"
            return self.response.decode('UTF-8')
        else:
            self.response = None
            self.corr_id = str(uuid.uuid4())
            #print("spedisco:"+str(self.corr_id))
            dataSEND = {"name":cmd["name"], "value":"", "type":"sync"}
            self.channel.basic_publish(exchange='',
                                       routing_key='hpsu_queue',
                                       properties=pika.BasicProperties(
                                             reply_to = self.callback_queue,
                                             priority=priority,
                                             correlation_id = self.corr_id,
                                             ),
                                       body=str(json.dumps(dataSEND)))
            timeout = 0
            while self.response is None and timeout <= 200:
                time.sleep(0.1)
                self.connection.process_data_events()
                timeout += 1
            #print(str(timeout))
            if timeout >= 200:
                self.response = b"KO"
            return self.response.decode('UTF-8')
    
