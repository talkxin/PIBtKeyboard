#!/bin/bash

__HOME=/home/pi/PIBtKeyboard/

#start Bluetooth daemon
__restartDaemon() {
    /etc/init.d/bluetooth stop
    /usr/sbin/bluetoothd --nodetach --debug -p time &
    hciconfig hcio up
    #简单配对模式
    hciconfig hci0 sspmode
    #开启匹配
    bluetoothctl agent on
    bluetoothctl default-agent
    bluetoothctl discoverable on
}

__connect() {
    cd ${__HOME}/service/
    python service.py $1 &

    sleep 2

    cd ${__HOME}/client/
    python client.py &
}

if [ $(whoami) = "root" ]; then
    export __HOME=${__HOME}
    if [ ! -n ${__RESTART} ]; then
        __restartDaemon
        export __RESTART=1
    fi
    __connect $1
fi
