#!/bin/bash
#set -x

# Format of argument: HH:MM:SS, with HH between 00 and 23.
secs_to_next_attractor()
{
    local next_time="$1"

    now=$(date -Iseconds)
    secs_now=$(date --date="$now" +"%s")
    ntime=$(echo $now | sed -e "s/[0-9][0-9]:[0-9][0-9]:[0-9][0-9]/$next_time/")
    secs_ntime=$(date --date="$ntime" +"%s")
    if [ $secs_ntime -lt $secs_now ]
    then
        echo $(($secs_ntime - $secs_now + 86400))
    else
        echo $(($secs_ntime - $secs_now))
    fi
}

echo "Attractor machine started."

while true
do
    cd /opt/attractors/web
    sleep "$(secs_to_next_attractor $1)"
    ./create_daily.py -j$(nproc) -R/opt/attractors/html 2>&1
done

