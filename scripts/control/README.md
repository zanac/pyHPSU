# Control Scripts
Scripts to automatically control HPSU.
## Chrono-thermostat

Set of useful scripts to automatically control:
* heating timeframe
* cooling timeframe
* heating setpoints
* cooling setpoints

## Flow Temperature Control

Scripts to control heating flow temperature:
* PI Controller (inside temperature vs setpoint)
* heating power control within HPSU specifications

## DHW / Cooling Setpoint Scheduling

* Scripts to schedule DHW/Cooling setpoints settings:
** DHW Setpoint (set_T-ACS1.py)
** DHW Hysteresis (set_IsteresiACS.py)
** Cooling Setpoint (set_T-ImpRefrig.py)

* Scripts to schedule various HPSU Operating Mode changes:
** Summer Mode (setmode_Estate.py)
** Cooling Mode (setmode_Raffrescare.py)
** Heating Mode (setmode_Riscaldare.py)

## To-do list
* Make all configuration parameters external
* Include DHW control inside chrono-thermostat (currently in crontab)
* Create cooling flow temperature control (nice to have)
