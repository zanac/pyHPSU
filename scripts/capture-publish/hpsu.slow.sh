#! /bin/bash
python3 /usr/share/pyHPSU/bin/pyHPSU.py -d PYCAN -c qboh -c qchhp -c qch -c qwp -c qdhw -c t_dhw_setpoint1 -c hyst_hp -c t_dhw_set -o CLOUD -u EMONCMS -g /var/log/hpsu.slow.log -v 1
