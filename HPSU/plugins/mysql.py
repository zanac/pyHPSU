#!/usr/bin/env python3



# Entries in pyhpsu.conf
# [MYSQL]
# DB_HOST = localhost
# DB_PORT = 3306
# DB_NAME = HPSU
# DB_USER = HPSU_USER
# DB_PASSWORD = HPSU_PASSWORD

import mysql.connector
from mysql.connector import errorcode
import configparser
import sys
import os
from distutils.version import StrictVersion

class db():
    hpsu = None

    def __init__(self, hpsu=None, logger=None, config_file=None, config=None):
        self.hpsu = hpsu
        self.logger = logger
        self.config = config
        self.config_file=config_file
        self.db_version = None

       
        db_config = configparser.ConfigParser()
        if not self.config_file:
            self.config_file="/etc/pyHPSU/pyHPSU.conf"
    
        if os.path.isfile(self.config_file):
            db_config.read(self.config_file)
        else:
            sys.exit(9)
        if db_config.has_option('MYSQL','DB_HOST'):
            db_host=db_config['MYSQL']['DB_HOST']
        else:
            db_host="localhost"

        if db_config.has_option('MYSQL','DB_PORT'):
            db_port=db_config['MYSQL']['DB_PORT']
        else:
            db_port="3306" 
        
        if db_config.has_option('MYSQL','DB_NAME'):
            db_name=db_config['MYSQL']['DB_NAME'] 
        else:
            self.hpsu.logger.error("No database name defined in config file .")
            sys.exit(9)

        if db_config.has_option('MYSQL','DB_USER'):
            db_user=db_config['MYSQL']['DB_USER']
        else: 
            self.hpsu.logger.error(("No database user defined in config file.")
            sys.exit(9)

        if db_config.has_option('MYSQL','DB_PASSWORD'):
            db_password=db_config['MYSQL']['DB_PASSWORD']
        else:
            self.hpsu.logger.error("No password for the database user defined in config file")
            sys.exit(9)
        
        self.db_params={ 'host':db_host, 'port':db_port, 'user':db_user, 'password':db_password, 'database':db_name } 

        try:
            self.db_conn= mysql.connector.connect(**self.db_params)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.hpsu.logger.error("Username or password wrong")
                sys.exit(9)
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.hpsu.logger.error("Database does not exist")
                sys.exit(9)
        else:
            self.db_conn.close()
            #self.hpsu.logger.debug("Closed")
        self.check_commands_db()

    def check_commands_db(self):

        # gets command from a dict HPSU created
        # Looks, if a version id could be found
        # if not or version_id is higher then in DB, commands are put into DB
        self.commands_file_version=self.hpsu.all_commands["version"]
        self.db_conn= mysql.connector.connect(**self.db_params)
        cursor=self.db_conn.cursor()
        cursor.execute("SELECT descr from commands WHERE name = 'version'")
        commands_db_version=cursor.fetchall()
        if commands_db_version:
            self.db_version=commands_db_version[0][0]
        
        # if no version info is found in DB
        if self.db_version:
            # update the version if a newer is available in commands_hpsu.csv
            if StrictVersion(self.commands_file_version) > StrictVersion(self.db_version):
                UpdateQuery="UPDATE commands SET descr='%s' WHERE name='%s'" %  (self.hpsu.command_dict['version']['desc'],self.hpsu.command_dict['version']['name'])
                cursor.execute(UpdateQuery)
                # update all commands or insert the new ones
                self.update_db(cursor)
        
        else:
            # insert version info
            InsertQuery="INSERT INTO commands (name,descr) VALUES ('%s','%s')" %  (self.hpsu.command_dict['version']['name'],self.hpsu.command_dict['version']['desc'])
            cursor.execute(InsertQuery)
            # and insert all the commands   
            self.update_db(cursor)
        self.db_conn.commit()
        cursor.close()
        self.db_conn.close()

    def update_db(self,cursor):
        # and update all commands or insert the new ones
        for com in self.hpsu.command_dict:
            if com not in "version":
                n_name=self.hpsu.command_dict[com]['name']
                n_desc=self.hpsu.command_dict[com]['desc']
                n_command=self.hpsu.command_dict[com]['command']
                n_label=self.hpsu.command_dict[com]['label']
                n_receiver_id=self.hpsu.command_dict[com]['receiver_id']
                n_um=self.hpsu.command_dict[com]['um']
                n_div=self.hpsu.command_dict[com]['div']
                n_flagRW=self.hpsu.command_dict[com]['flagRW']
                # insert new commands
                UpdateQuery="INSERT INTO commands (name,descr,label,command,receiver_id,um,divisor,readwrite) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s') on DUPLICATE KEY UPDATE descr='%s', command='%s', label='%s', receiver_id='%s', um='%s', divisor='%s', readwrite='%s'" % (n_name,n_desc,n_label,n_command,n_receiver_id,n_um,n_div,n_flagRW,n_desc,n_command,n_label,n_receiver_id,n_um,n_div,n_flagRW)
                cursor.execute(UpdateQuery)
                # insert table for each command
                TableQuery="CREATE TABLE IF NOT EXISTS `%s` (`id` int(20) NOT NULL PRIMARY KEY AUTO_INCREMENT,`value` float NOT NULL,`timestamp` varchar(20) COLLATE utf8_bin NOT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;" % (n_name)
                cursor.execute(TableQuery)
    
    def pushValues(self,vars=None):
        self.push_conn= mysql.connector.connect(**self.db_params)
        cursor=self.push_conn.cursor()
        for reply in vars:
            PushQuery="INSERT INTO commands (name, current_value, timestamp) VALUES ('%s', '%s','%s') on DUPLICATE KEY UPDATE current_value='%s', timestamp='%s'" % (reply['name'], reply['resp'], reply['timestamp'], reply['resp'], reply['timestamp'])
            cursor.execute(PushQuery)
            PushValueQuery="INSERT INTO %s (value,timestamp) VALUES ('%s','%s')" % (reply['name'],reply['resp'],reply['timestamp'])
            cursor.execute(PushValueQuery)
        self.push_conn.commit()
        cursor.close()
        self.push_conn.close()

   


if __name__ == '__main__':
    app = db()
    
    app.exec_()