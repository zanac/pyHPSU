#! /bin/bash
python3 /home/pi/pyHPSU-master/pyHPSU.py -d PYCAN -c t_hc_set -c t_dhw_set -c t_ext -c t_outdoor_ot1 -c ta2 -o CLOUD -u EMONCMS -g /home/pi/hpsu.medium.log -v 1
