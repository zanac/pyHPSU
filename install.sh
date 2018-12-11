#!/bin/bash

SHARE_DIR="/usr/share/pyHPSU/"
CONF_DIR="/etc/pyHPSU"
BIN_DIR="/usr/bin/"
PACKAGE_DIR="/usr/share/doc/packages/pyHPSU"
DIST_DIR="/usr/lib/python3/dist-packages/HPSU"
SYSTEMD_DIR="/etc/systemd/system/hpsud.service"



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

if [ -d $SYSTEMD_DIR ]; then
	echo "Creting directory for systemd files"
	mkdir -p $SYSTEMD_DIR
fi

# copy configs
cp etc/pyHPSU/commands* $CONF_DIR/
if [ ! -f $CONF_DIR/pyhpsu.conf ]; then
	cp etc/pyHPSU/pyhpsu.conf $CONF_DIR/
else 
	cp etc/pyHPSU/pyhpsu.conf $CONF_DIR/pyhpsu.conf.new
fi


# copy the rest
#cp -r can $SHARE_DIR 
cp -r HPSU/* $DIST_DIR
cp -r scripts $PACKAGE_DIR
cp -r examples $PACKAGE_DIR
cp -r plugins $DIST_DIR

# copy service file
cp hpsud.service $SYSTEMD_DIR
if [ -x /bin/systemctl ]; then 
	systemctl --system daemon-reload
fi

# copy binarys
cp pyHPSU.py $BIN_DIR
cp pyHPSUd.py $BIN_DIR
chmod a+x $BIN_DIR/pyHPSU.py
chmod a+x $BIN_DIR/pyHPSUd.py

	