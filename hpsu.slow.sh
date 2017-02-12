#! /bin/bash
sudo /sbin/ip link set can0 up type can bitrate 20000
python3 /home/pi/pyHPSU-master/pyHPSU.py -d PYCAN -c qboh -c qchhp -c qch -c qwp -c qdhw -o CLOUD -u EMONCMS -g /home/pi/hpsu.slow.log -v 1
