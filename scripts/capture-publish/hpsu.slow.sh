#! /bin/bash
sudo /sbin/ip link set can0 up type can bitrate 20000
python3 /home/pi/pyHPSU-master/pyHPSU.py -d PYCAN -c qboh -c qchhp -c qch -c qwp -c qdhw -c t_dhw_setpoint1 -c hyst_hp -c t_dhw_set -c t_flow_cooling -o CLOUD -u EMONCMS -g /home/pi/log/hpsu.slow.log -v 1
