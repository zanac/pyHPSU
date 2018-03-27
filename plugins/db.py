#!/usr/bin/env python3


import mysql.connector
from mysql.connector import errorcode
import configparser
import sys
import os

class db():
    hpsu = None

    #def get_with_default(self, config, section, name, default):
    #   if "config" not in config.sections():
    #        return default
    #    
    #    if config.has_option(section,name):
    #        return config.get(section,name)
    #    else:
    #        return default

    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.hpsu = hpsu
        self.logger = logger

       
        db_config = configparser.ConfigParser()
        # confFile = '%s/db.conf' % (self.hpsu.pathCOMMANDS)
        if config_file:
            confFile=config_file
        else:
            confFile="../etc/pyHPSU/pyHPSU.conf"
        #try:
        #    with open(confFile) as file:
        #        print("Config found")
        #        pass
        #except FileNotFoundError as e:
        #    print("Unable to open file %s/db.conf\n ",  self.hpsu.pathCOMMANDS)
        #    sys.exit(9)
        if os.path.exists(confFile):
            db_config.read(confFile)
        else:
            print("mist....")
            sys.exit(9)
        if db_config.has_option('DATABASE','DB_HOST'):
            db_host=db_config['DATABASE']['DB_HOST']
        else:
            db_host="localhost"

        if db_config.has_option('DATABASE','DB_PORT'):
            db_port=db_config['DATABASE']['DB_PORT']
        else:
            db_port="3306" 
        
        if db_config.has_option('DATABASE','DB_NAME'):
            db_name=db_config['DATABASE']['DB_NAME'] 
        else:
            print("No database name defined.")
            sys.exit(9)

        if db_config.has_option('DATABASE','DB_USER'):
            db_user=db_config['DATABASE']['DB_USER']
        else: 
            print("No database user defined.")
            sys.exit(9)

        if db_config.has_option('DATABASE','DB_PASSWORD'):
            db_password=db_config['DATABASE']['DB_PASSWORD']
        else:
            print("No password for the database user defined")
            sys.exit(9)
        
        db_config={ 'host':db_host, 'port':db_port, 'user':db_user, 'password':db_password, 'database':db_name } 

        try:
            db_conn= mysql.connector.connect(**db_config)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Username or password wrong")
                sys.exit(9)
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                sys.exit(9)


        

if __name__ == '__main__':
    app = db()
    
    app.exec_()