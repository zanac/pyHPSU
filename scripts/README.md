# Scripts

## Capture-Publish

Set of useful scripts to automatically read from HPSU Compact and publish them on the cloud ([emoncms.org](http://emoncms.org)) a configurable list of variables.
Copy the *.service and the *.timer to /etc/systemd/system and enable and
start it via systemctl (e.g. "systemctl enable hpsu.fast.timer" and and
"systemctl start hpsu.fast.timer") 

## Control

Scripts to automatically control HPSU:
* Chrono-thermostat (heating and cooling)
* Flow Temperature Control (heating only)
* DHW / Cooling Setpoint Scheduling
