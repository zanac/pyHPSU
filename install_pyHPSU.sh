#!/bin/bash

SHARE_DIR="/usr/share/pyHPSU/"
CONF_DIR="/etc/pyHPSU"


if [ ! -d $CONF_DIR ]; then
        echo "Creating directory for config files"
        mkdir -p $CONF_DIR
fi

if [ ! -d $SHARE_DIR ]; then
	echo "Creating directory for shared files"
	mkdir -p $SHARE_DIR
fi


# copy configs
cp etc/pyHPSU/EMONCMS.ini $CONF_DIR/emoncms.ini
cp etc/pyHPSU/canpi.ini $CONF_DIR/canpi.ini
cp etc/pyHPSU/commands* $CONF_DIR/
cp etc/pyHPSU/pyhpsu.conf $CONF_DIR/

# copy the rest
cp -r can $SHARE_DIR 
cp -r HPSU $SHARE_DIR
cp -r scripts $SHARE_DIR
cp -r examples $SHARE_DIR
cp -r plugins $SHARE_DIR

# copy service file
cp hpsud.service /etc/systemd/system/
systemctl --system daemon-reload

	