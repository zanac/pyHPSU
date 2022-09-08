# Scripts

## Capture-Publish

Set of useful scripts to automatically read from HPSU Compact and publish them on the cloud ([emoncms.org](http://emoncms.org)) a configurable list of variables.

Copy <code>*.service</code> and <code>*.timer</code> files to <code>/etc/systemd/system</code> directory and enable and start it via <code>systemctl>/code>.

Examples:
<code>sudo systemctl enable hpsu.fast.timer</code>
<code>sudo systemctl start hpsu.fast.timer</code>

## Control

Scripts to automatically control HPSU:
* Chrono-thermostat (heating and cooling)
* Flow Temperature Control (heating only)
* DHW / Cooling Setpoint Scheduling
