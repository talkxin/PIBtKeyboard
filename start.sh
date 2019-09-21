#!/bin/bash

__HOME=/opt/PIBtKeyboard/

#start Bluetooth daemon
__restartDaemon(){
    /etc/init.d/bluetooth stop
    /usr/sbin/bluetoothd --nodetach --debug -p time &
    hciconfig hcio up
    #简单配对模式
    hciconfig hci0 sspmode
}

cd ${__HOME}/service/
python service.py &

cd ${__HOME}/client/
python client.py