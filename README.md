# BauerPrint

###
Thermal printing at home. This program is meant to be used on a _RaspberryPi_ plugged on a thermal printer (tested on a _Excelvan HOP-E801_) with a **USB/Serial interface**.

This repository contains the **`Home Printer`** package to interface with your thermal printer and a `flask` server launcher (see `script\main.py`).

### Installation notes
- On the Raspberry please install `sudo apt install libwebp-dev` 
- Don't forget to run `chmod +x launchFlaskServer.sh && && chmod +x launchTelegramClient.sh && chmod +x inspireSom.sh && chmod +x printMenageNyass.sh && sudo ln -s /home/pi/BauerPrint/bauerprint.service /etc/systemctl/system/bauerprint.service && sudo systemctl enable bauerprint.service && sudo ln -s /home/pi/BauerPrint/facks-machine.service /etc/systemctl/system/facks-machine.service && sudo systemctl enable facks-machine.service`, and add in `sudo crontab -e` : 
    -`48 2 * * 1 sh /home/facks/Desktop/BauerPrint/printMenageNyass.sh`.
    -`0 7 * * * sh /home/facks/Desktop/BauerPrint/inspireSom.sh`.
    -`30 3 * * 0,2,4,6  reboot`
    -`@reboot sh /home/facks/Desktop/BauerPrint/voicemail.sh`.

### Development notes

- _Windows_ can run the `flask` server, but will not print (the scripts needs a `/dev/ttyUSB%d` character block for that). 
- Need to downgrade to `pip==19.3.1` in order to `pip install Pillow` on _Windows_. Other packages are fine with latest version of `pip`.