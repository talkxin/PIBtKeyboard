#!/bin/bash

__HOME=/home/pi/PIBtKeyboard/

cd ${__HOME}
sh stop.sh
sleep 2
sh start.sh -i
