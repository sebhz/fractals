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

create_attractor()
{
    cd /opt/attractors/web
    ./create_daily.py -j$(nproc) -R/opt/attractors/html 2>&1
}

usage()
{
    echo "$0 mode [generation_time]"
    echo "  mode can be either 'oneshot' or 'continuous'"
    echo "  generation_time applies only in continuous mode. Format HH:MM:SS with 00<=HH<=23"
}

mode=$1; shift
case $mode in
    "")
        mode="oneshot"
        ;;
    oneshot|continuous)
        ;;
    *)
        usage
        exit
        ;;
esac

if [ "$mode" == "continuous" ]
then
    ttna=$1
    if [ "$ttna" == "" ]
    then
        ttna="00:00:00"
    fi
fi

echo "Attractor machine started."
if [ "$mode" == "oneshot" ]
then
    create_attractor
elif [ "$mode" == "continuous" ]
then
    while true
    do
        next_sec="$(secs_to_next_attractor $ttna)"
        echo "Next attractor generation will occur in $next_sec seconds."
        sleep "$next_sec"
        create_attractor
    done
fi

