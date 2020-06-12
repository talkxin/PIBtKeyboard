#!/bin/bash

service=`ps -aux | grep "service.py" | awk 'NR==1{print $2}'`
client=`ps -aux | grep "client.py" | awk 'NR==1{print $2}'`

kill -9 ${service}
kill -9 ${client}