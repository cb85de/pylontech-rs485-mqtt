

# Installation on Raspberry Pi
Ensure python packages are installed:
`sudo apt-get install python3-full python3-serial python-setuptools python3-setuptools`

## Configure Raspberry Pi RS485 Hat 
Following https://www.waveshare.com/wiki/RS485_CAN_HAT


## Install lgpio is a library for Linux Single Board Computers / RaspberryPI Zero
```bash
wget https://github.com/joan2937/lg/archive/master.zip
unzip master.zip
cd lg-master
make
sudo make install
```


# Setting up Python environment and prepare libary
For communication with the pylontech battery, I used the python class from https://github.com/Frankkkkk/python-pylontech
```bash
python3 -m venv pylontech-monitor/
pylontech-monitor/bin/pip install -r requirements.txt
```




