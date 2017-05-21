# Control Scripts
Scripts to automatically control HPSU.
## Chrono-thermostat

Set of useful scripts to automatically control:
* heating/cooling timeframe
* heating/cooling setpoints

## Flow Temperature Control

Scripts to control heating flow temperature:
* PI Controller (inside temperature vs setpoint)
* heating power control within HPSU specifications

## Operating Mode / Setpoints Scheduling

* Scripts to schedule HPSU Operating Mode settings
* Scripts to schedule Cooling/DHW/Heating setpoints settings
* Crontab example

## To-do list
- [ ] Make all configuration parameters external
- [ ] Include DHW control inside chrono-thermostat (currently in crontab)
- [ ] Create cooling flow temperature control (nice to have)
- [ ] Create smarter DHW setpoint temperature control (nice to have)
