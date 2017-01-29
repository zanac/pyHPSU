#! /bin/bash
sudo /sbin/ip link set can0 up type can bitrate 20000
cd /home/pi/pyHPSU-master/HPSU
while true; do
    python3 ../pyHPSU.py -d PYCAN -c t_hc -c t_return -c flow_rate -c mode -c bpv -c posmix -c t_dhw -c t_v1 -c t_dhw1 -c t_vbh -c t_r1 -c tvbh2 -c tliq2 -c tr2 -c tdhw2 -c ehs -c pump -o CLOUD -u EMONCMS
    sleep 10
done
