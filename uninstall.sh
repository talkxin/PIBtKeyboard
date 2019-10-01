#!/bin/bash

__SYSTEMCTL_PATH=/usr/lib/systemd/system/
__SYSTEMD=/etc/dbus-1/system.d/
__SERVICE_NAME=bluekeyboard.service
DBUS_NAME=org.btservice.keyboard.conf


systemctl disable ${__SERVICE_NAME}

rm -rf ${__SYSTEMD}/${DBUS_NAME}
rm -rf ${__SYSTEMCTL_PATH}/${__SERVICE_NAME}