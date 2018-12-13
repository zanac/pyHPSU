# Welcome to pyHPSU
pyHPSU is a set of python scripts and other files to read and modify the values of the Rotex® HPSU (possibly) also identical heating pumps from daikin®).

**Using pyHPSU may cause _damage_ to the heating system. The use of pyHPSU is at your own risk. The creator can not be held responsible for damage.**

**You may risk a loss of warranty and support from the manufacturer!!!!**

**This software is not supported by the manufacturer!!!!**


It is based on the idea and the work of 
 **[Vanni Brutto alias Zanac](https://github.com/zanac/pyHPSU)**

It is expandable via plugins to send data to other systems and databases.
At the momeent, Emoncms, fhem, homematic and mysql are supported.

It works with [SocketCan](https://elinux.org/CAN_Bus) __OR__ the [elm327](https://en.wikipedia.org/wiki/ELM327) based serial-can interfaces.  
The advantage of SocketCan: it can handle multiple instances or programs talking over the same can interface or you can query multiple values with one command. Message queuing is done by the kernel. For serial can interfaces (like the Elm327) you need a server which handles the messages. To do this, pyHPSUd.py is there. It handles multiple pyHPSU.py session via rabbitMQ.


## Hardware setup
1. Via Elm327 interface
- Most cheap china replicas will not work because the "AT PP" command is not implemented. A purchase recommendation is as follows: https://www.totalcardiagnostics.com/elm327
- It is recommended to order a matching obd2 socket (16pol) to connect the can adapter
- Connect the CAN-High cable pin 6, the CAN-Low cable pin 14 and CAN signal ground pin 5 to the hpsu mainboards "J13" connector. (Power on the CAN-Side is not needed)
- look at your systems "dmesg" while  connecting to get the device name 

2. SocketCan
- connect the Pins from the HPSU mainboards "J13" connector to the pins of your can interface. Needed are canH, canL and ground.
- for debian (and other systems) and the following to /etc/network/interfaces:

auto can0  
iface can0 inet manual  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pre-up /sbin/ip link set $IFACE type can bitrate 20000 triple-sampling on  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;up /sbin/ifconfig $IFACE up  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;down /sbin/ifconfig $IFACE down



## Software setup

pyHPSU only runs on unix/linux based systems.
1. To run pyHPSU you need:
- python3
- python3-can
- python3-serial
- python3-pika
- python3-requests
- python3-mysql.connector (used by the db plugin)
- python3-urllib3 (used by the homematic plugin)

2. git clone https://github.com/Spanni26/pyHPSU
3. cd pyHPSU
4. chmod +x install.sh
5. sh install.sh

## Using pyHPSU  
#### PyHPSU defaults:
- can-device: SocketCan (Driver canpi, for elm327 specify the driver with -d canelm327 and the line with e.g. -p /dev/ttyUSB )
- OutputFormat: JSON (other formats or output devices can be specified with "-o", the usage via "pyHPSU.py -?")

To get a list of all available commands call:  
root@rotex:~# pyHPSU.py -h

To get a bit more information about a single command:  
root@rotex:~# pyHPSU.py -h -c \<command>  
e.g.
root@rotex:~# pyHPSU.py -h -c t_hs  

To query a value (e.g. t_hs):
root@rotex:~# pyHPSU.py -c t_hs

The default setting is the output to the console in json format, so the output will look like this:
[{'name': 't_hs', 'resp': '32.00', 'timestamp': 1544534667.414178}]


#### Output options ("-o \<output>"):
- CSV:
Output is send to console in CSV format (comma separated value)

- DB:
If a database should be used simply create a mysql DB with collation "utf8_bin", edit the pyhpsu.conf and select "DB" as output type
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/db.py to find a template)

- EMONCMS:
Send the data to an emoncms instance (locally or the web version)
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/emoncms.py to find a template)

- FHEM:
Send the data to a fhem instance. Atm only pushing the values via telnet to port 7072 is supported.
Configure it in /etc/pyHPSU/pyhpsu.conf (look ath the code of /usr/lib/python3/dist-packages/HPSU/fhem.py to find a template)

- HOMEMATIC:
Send the data to homematic. Therefore the xmlapi has to be installed on the ccu, a system variable has to be configured and the ise_id of this variable must be configured in the pyHPSU.conf. Look ath the code of /usr/lib/python3/dist-packages/HPSU/fhem.py to find a template

#### Modes:
pyHPSU.py can be run un different modes.
1. Standalone
You can run the pyHPSU.py in standalone mode forom the command line.  
e.g. query the value of t_hs, output in CSV format, using an elm327 interface on port /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0  
root@rotex:~# pyHPSU.py -c t_hs -d elm327 -p /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_-if00-port0 -o CSV  
e.g. ask the heating pump for an pending error, output in JSON format, using an SocketCan interface  
root@rotex:~# pyHPSU.py -c error -o JSON -d canpi  
or simply (cause JSON and canpi are the defaults):  
root@rotex:~# pyHPSU.py -c error

2. Auto Mode
The pyHPSU.py can be run in "auto mode". You can define values which should be querried in different periods. This is done at /etc/pyHPSU/pyhpsu.conf.  
At the "jobs" section add the value and the period (as shown by the examples) and addopt the section "PYHPSU" to your needs. Then, run the pyHPSU.py with the parameter "-a"  
e.g.  
root@rotex:~# pyHPSU.py -a 

3. With Message Broker (only needed with serial intrerfaces like Elm327)  
A serial line can only be used by one process at a time. So, if you query more then one value at a time or you run multiple instances of pyHPSU.py you can run in errors.  
In this mode, every query from pyHPSU.py is sent to the pyHPSUD.py. This daemon deals with the message broker "rabbitmq" which sends one query at a time and sorts the answers to the correct sending process.  
For that,install the message broker "rabbitmq".
You also have to configure the config file /etc/pyHPSU/pyhpsu.conf at section "PYHPSUD".  
Here, specify the driver, language and serial port to use.  
The pyHPSUD.py is started via systemd:  
root@rotex:~# systemctl enable hpsud.service  
root@rotex:~# systemctl start hpsud.service  
Now, you can query multiple values or run multiple pyHPSU.py processes. Simply set as driver "CANTCP" via commandline or the config file (PYHPSU section)


