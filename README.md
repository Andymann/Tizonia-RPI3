# Tizonia-on-Raspberry-Pi

Function | Pin | Signal<br>
Skip | 11 | Gpio 17<br>
PL 0 | 08 | Gpio 14<br>
PL 1 | 10 | Gpio 15<br>
PL 2 | 12 | Gpio 18<br>
PL 3 | 16 | Gpio 23<br>
PL 4 | 18 | Gpio 24<br>

In order for everything to work you need to configure the RPI to automatically boot into a desktop environment (via raspi-config -> boot options).
In order to run without an external monitor you need to add

export DISPLAY=":0"

at the end of .bashrc .
