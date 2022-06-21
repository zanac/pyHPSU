#!/bin/bash

SHARE_DIR="/usr/share/pyHPSU/"
CONF_DIR="/etc/pyHPSU"
BIN_DIR="/usr/bin/"
PACKAGE_DIR="/usr/share/doc/packages/pyHPSU"
DIST_DIR="/usr/lib/python3/dist-packages/HPSU"
SERVICE_DIR="/etc/systemd/system/"
echo "Installing pyHPSU"
if [ ! -d $CONF_DIR ]; then
        echo "Creating directory for config files"
        mkdir -p $CONF_DIR
fi

if [ ! -d $PACKAGE_DIR ]; then
	echo "Creating directory for shared files"
	mkdir -p $PACKAGE_DIR
fi

if [ ! -d $BIN_DIR ]; then
	echo "Creating directory for executable files"
	mkdir -p $BIN_DIR
fi

if [ ! -d $DIST_DIR ]; then
	echo "Creating directory for python includes files"
	mkdir -p $DIST_DIR
fi
if [ ! -d $SHARE_DIR ]; then
	echo "Creating directory for resource files"
	mkdir -p $SHARE_DIR
fi

# copy configs
cp etc/pyHPSU/commands* $CONF_DIR/
if [ -f /etc/pyHPSU/pyhpsu.conf ]; then
	cp etc/pyHPSU/pyhpsu.conf $CONF_DIR/pyhpsu.conf.new
else 
	cp etc/pyHPSU/pyhpsu.conf $CONF_DIR/
fi

# copy the rest
cp -r resources/* $SHARE_DIR 
cp -r HPSU/* $DIST_DIR
cp -r contrib $DIST_DIR

# copy service file
#cp systemd/* $SERVICE_DIR
#systemctl --system daemon-reload

# copy binarys
cp pyHPSU.py $BIN_DIR
cp pyHPSUd.py $BIN_DIR
chmod a+x $BIN_DIR/pyHPSU.py
chmod a+x $BIN_DIR/pyHPSUd.py

echo "Installation done!!!"

	
