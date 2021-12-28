#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# config inf conf_file (defaults):
# [INFLUXDB]
# HOST = hostname_or_ip
# PORT = 8086
# DB_NAME = pyHPSU

import configparser
import requests
import sys
import os
import datetime
import influxdb


class export():
    hpsu = None

    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.hpsu = hpsu
        self.logger = logger
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            self.config.read(self.config_file)
        else:
            sys.exit(os.EX_CONFIG)

        # influxdb hostname or IP
        if self.config.has_option('INFLUXDB', 'HOST'):
            self.influxdbhost = self.config['INFLUXDB']['HOST']
        else:
            self.influxdbhost = 'localhost'

        # influxdb port
        if self.config.has_option('INFLUXDB', 'PORT'):
            self.influxdbport = int(self.config['INFLUXDB']['PORT'])
        else:
            self.influxdbport = 8086

        # influxdb db name
        if self.config.has_option('INFLUXDB', 'DB_NAME'):
            self.influxdbname = self.config['INFLUXDB']['DB_NAME']
        else:
            self.influxdbname = "pyHPSU"



    def pushValues(self, vars=None):
        self.current_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        # create connection
        self.client = influxdb.InfluxDBClient(host=self.influxdbhost, port=self.influxdbport)
        # create database if it doesn't exist
        try:
            self.databases=self.client.get_list_database()
            db_found = False
            for db in self.databases:
                if db['name'] == self.influxdbname:
                    db_found = True
            if not(db_found):
                self.client.create_database(self.influxdbname)
               
        except:
            rc = "ko"
            self.hpsu.logger.exception("Error : Cannot connect to database")


        self.client.switch_database(self.influxdbname)

        for dict in vars:

            self.value_dict=[{
                "measurement": "pyHPSU",
                "tags":{
                },
                "fields": {
                     dict["name"] : dict["resp"]
                    }
                }
            ]

            self.client.write_points(self.value_dict)
            


    #if __name__ == '__main__':
    #    app = influxdb()

    #    app.exec_()
