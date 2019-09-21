#!/bin/bash

__HOME=/opt/PIBtKeyboard/

#start Bluetooth daemon
__restartDaemon(){
    /etc/init.d/bluetooth stop
    /usr/sbin/bluetoothd --nodetach --debug -p time &
    hciconfig hcio up
    #简单配对模式
    hciconfig hci0 sspmode
    #开启匹配
    bluetoothctl agent on
    bluetoothctl default-agent
    bluetoothctldiscoverable on
}

__restartDaemon

cd ${__HOME}/service/
python service.py &

sleep 2

cd ${__HOME}/client/
python client.py