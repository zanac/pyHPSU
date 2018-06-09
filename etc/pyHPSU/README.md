## Configuration files

- <code>commands_hpsu.csv</code>

It includes the main technical dictionary with HPSU variables names and actual CAN Bus values. Practically to be never modified unless you want to add a new variable not sniffed

- <code>commands_hpsu_XX.csv</code>

Human readable list of variables translated in few language.
Basically useless but the application could not work if the file corresponding to your locale does not exist.
File content has to be aligned with <code>commands_hpsu.csv</code> one.

- <code>EMONCMS.ini</code>

Configuration and dictionary file to publish data on emoncms.org service.

