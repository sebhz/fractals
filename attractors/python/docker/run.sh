#!/bin/bash

cd /opt/attractors/web
./create_daily.py -R /opt/attractors/html >>/var/log/attractors.log 2>&1

