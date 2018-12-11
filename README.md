pyHPSU is a set of python scripts and other files to read and modify the values of the Rotex® HPSU (possibly) also identical heating pumps from daikin®).

#############################################################################################################################################################
>>>>>>> Using pyHPSU may cause damage to the heating system. The use of pyHPSU is at your own risk. The creator can not be held responsible for damage. <<<<<
>>>>>>> You may risk a loss of warranty and support from the manufacturer!!!!
>>>>>>> This software is not supported by the manufacturer!!!! 
#############################################################################################################################################################
It is based on the idea and the work of

Vanni Brutto alias Zanac (https://github.com/zanac/pyHPSU)

It is expandable via plugins to send data to other systems and databases.
At the momeent, Emoncms, fhem, homematic and mysql are supported.

It works with SocketCan and the Elm327 usb-serial-can interface.

---- Installation ----
pyHPSU only runs on linux based systems.
To run pyHPSU you need:
- python3
- python3-can
- python3-serial
- python3-pika
- python3-requests
- python3-mysql.connector (used by the db plugin)
- python3-urllib3 (used by the homematic plugin)

Extract the zip and run "sh install.sh"

---- Connection ----
The HPSU can be connected via the can protocol at connector "J13" at the Rocon BM1 mainboard.
Connect Can-H, Can-L and Can-GND  to your can adapter, for SocketCan set up the can device.



---- Using pyHPSU ----
PyHPSU defaults:
- can-device: SocketCan (Driver canpi, for elm327 specify the driver with -d canelm327 and the line with e.g. -p /dev/ttyUSB )
- OutputFormat: JSON (other formats or output devices can be specified with "-o", the usage via "pyHPSU.py -?")

To get a list of all available commands call:
root@rotex:~# pyHPSU.py -h

To get a bit more information about a single command:
root@rotex:~# pyHPSU.py -h -c <command>
e.g.
root@rotex:~# pyHPSU.py -h -c t_hs

To query a value (e.g. t_hs):
root@rotex:~# pyHPSU.py -c t_hs

The default setting is the output to the console in json format, so the output will look like this:
[{'name': 't_hs', 'resp': '32.00', 'timestamp': 1544534667.414178}]


Output ("-o <output>):
- CSV:
Output is send to console in CSV format (comma separated value)

- DB:
If a database should be used simply create a mysql DB with collation "utf8_bin", edit the pyhpsu.conf and select "DB" as output type
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/db.py to find a template)

- emoncms:
Send the data to an emoncms instance (locally or the web version)
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/emoncms.py to find a template)

- fhem.py:
Send the data to a fhem instance. Atm only pushing the values via telnet to port 7072 is supported.
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/fhem.py to find a template)

- homematic.py:
Send the data to homematic. Therefore the xmlapi has to be installed on the ccu, a system variable has to be configured and the ise_id of this variable must be configured in the pyHPSU.conf. Look ath the code of /usr/lib/python3/dist-packages/HPSU/fhem.py to find a template