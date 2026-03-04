# BauerPrint

###
Thermal printing at home. This program is meant to be used on a _RaspberryPi_ plugged on a thermal printer (tested on a _Excelvan HOP-E801_) with a **USB/Serial interface**.

This repository contains the **`Home Printer`** package to interface with your thermal printer and a `flask` server launcher (see `script\main.py`).

### Installation notes
- Please name the default user name on your raspberry to `facks` and clone this repo the raspberry's `Desktop`
- On the Raspberry please install `sudo apt install libwebp-dev` 
- Also please add a file named `/etc/asound.conf` with
    ```
    defaults.pcm.card 1
    defaults.ctl.card 1
    ```  
- In `sudo crontab -e` write at the end of the file:
     ``` 
    48 2 * * 1 sh /home/facks/Desktop/BauerPrint/printMenageNyass.sh
    0 7 * * * sh /home/facks/Desktop/BauerPrint/inspireSom.sh
    30 3 * * 0,2,4,6  reboot
    @reboot sh /home/facks/Desktop/BauerPrint/voicemail.sh
    ```
- Don't forget to run 
     ```
    cd ~/Desktop/BauerPrint && chmod +x launchFlaskServer.sh && && chmod +x launchTelegramClient.sh && chmod +x inspireSom.sh && chmod +x printMenageNyass.sh && chmod +x voicemail.sh
    sudo cp /home/facks/Desktop/BauerPrint/bauerprint.service /lib/systemd/system/bauerprint.service &&  sudo cp /home/facks/Desktop/BauerPrint/facks-machine.service /lib/systemd/system/facks-machine.service
    sudo systemctl enable bauerprint.service && sudo systemctl enable facks-machine.service
    sudo reboot
    ```  

### Development notes

- _Windows_ can run the `flask` server, but will not print (the scripts needs a `/dev/ttyUSB%d` character block for that). 
- Need to downgrade to `pip==19.3.1` in order to `pip install Pillow` on _Windows_. Other packages are fine with latest version of `pip`.