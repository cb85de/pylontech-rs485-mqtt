
Following https://www.waveshare.com/wiki/RS485_CAN_HAT

sudo apt-get install python3-full python3-serial python-setuptools python3-setuptools

# Install lgpio is a library for Linux Single Board Computers / RaspberryPI Zero
wget https://github.com/joan2937/lg/archive/master.zip
unzip master.zip
cd lg-master
make
sudo make install


https://github.com/Frankkkkk/python-pylontech


python3 -m venv pylontech-monitor/

wget https://github.com/Frankkkkk/python-pylontech/archive/refs/heads/master.zip
unzip master.zip

pylontech-monitor/bin/pip install -e ../python-pylontech-master

