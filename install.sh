#!/bin/bash

#安装脚本参考如下博客：
#https://qiita.com/mt08/items/5f9dfc30707f94e3b8c8
#https://impythonist.wordpress.com/2014/02/01/emulate-a-bluetooth-keyboard-with-the-raspberry-pi/
#http://yetanotherpointlesstechblog.blogspot.no/2016/04/emulating-bluetooth-keyboard-with.html
#https://github.com/yaptb/BlogCode
#并基于yaptb的源码进行改造输出而成

#判断是否已经安装过程序，即判断dbus配置文件是否安装至相应目录

DBUS_NAME=org.btservice.keyboard.conf

__HOME=/home/pi/PIBtKeyboard/
__BLUETOOTH_CONF=/etc/bluetooth/main.conf

__SYSTEMCTL_PATH=/usr/lib/systemd/system/

__SYSTEMCTL_TARGET=/lib/systemd/system/ctrl-alt-del.target

#realy software
__install_software() {
    echo "install software"
    apt-get update
    apt-get install -y python-gobject bluez bluez-tools bluez-firmware python-bluez python-dev python-pip python-dbus
    apt-get install -y crudini
    pip install evdev
    pip install ConfigParser
}

if [ ! -f "/etc/dbus-1/system.d/"${DBUS_NAME} ]; then
    echo "installing blue_keyboard"s
    __install_software
    cp ${__HOME}/dbus/${DBUS_NAME} /etc/dbus-1/system.d/

    #Shield Ctrl+Alt+Del
    mv ${__SYSTEMCTL_TARGET} ${__SYSTEMCTL_TARGET}.bak
    ln -s /dev/null ${__SYSTEMCTL_TARGET}
    systemctl daemon-reload

    #change bluetooth conf
    crudini --del $__BLUETOOTH_CONF General Class
    crudini --del $__BLUETOOTH_CONF General Name
    crudini --set $__BLUETOOTH_CONF General Class 0x002540
    crudini --set $__BLUETOOTH_CONF General Name PiZW_BTKb

    #systemctl enable btkb
    chmod 777 start.sh
    chmod 777 stop.sh
    chmod 777 restart.sh
    mkdir -p $__SYSTEMCTL_PATH
    cp service/bluekeyboard.service $__SYSTEMCTL_PATH
    systemctl enable bluekeyboard.service
    echo "the blue_keyboard is installed"

else
    echo "the blue_keyboard is installed"
fi

#start
sh ${__HOME}/start.sh
