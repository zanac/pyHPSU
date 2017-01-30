#! /bin/bash
sudo /sbin/ip link set can0 up type can bitrate 20000
cd /home/pi/pyHPSU-master/HPSU
while true; do
    python3 ../pyHPSU.py -d PYCAN -c qboh -c qchhp -c qch -c qwp -c qdhw -o CLOUD -u EMONCMS
    sleep 293
done
