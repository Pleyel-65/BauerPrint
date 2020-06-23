# BauerPrint

###
Thermal printing at home. This program is meant to be used on a _RaspberryPi_ plugged on a thermal printer (tested on a _Excelvan HOP-E801_) with a **USB/Serial interface**.

This repository contains the **`Home Printer`** package to interface with your thermal printer and a `flask` server launcher (see `script\main.py`).

### Developpent notes

- _Windows_ can run the `flask` server, but will not print (the scripts needs a `/dev/ttyUSB%d` character block for that) 
- Need to downgrade to `pip==19.3.1` in order to `pip install Pillow` on _Windows_. Other packages are fine with latest version of `pip`.