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

__research() {
    hciconfig hci0 sspmode
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
    while getopts "n:isd" arg; do
        case $arg in
        i)
            __restartDaemon
            __connect "default"
            ;;
        n)
            __connect $OPTARG
            ;;
        s)
            __research
            __connect "search"
            ;;
        d)
            __connect "default"
            ;;
        ?)
            echo "unkonw argument"
            exit 1
            ;;
        esac
    done
fi
