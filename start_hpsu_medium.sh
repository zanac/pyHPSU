#! /bin/bash
sudo /sbin/ip link set can0 up type can bitrate 20000
cd /home/pi/pyHPSU-master/HPSU
while true; do
    python3 ../pyHPSU.py -d PYCAN -c t_hc_set -c t_dhw_set -c t_ext -c t_outdoor_ot1 -c ta2 -o CLOUD -u EMONCMS
    sleep 61
done
