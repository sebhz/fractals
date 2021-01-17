#!/bin/bash

cd /opt/attractors/web/hugo
./create_daily.py -p /opt/attractors/html >>/var/log/attractors.log 2>&1

