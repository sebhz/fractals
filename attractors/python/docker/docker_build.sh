#!/bin/bash

usage()
{
    echo "$0 <basic|hugo>"
}

if [ "$#" -ne 1 ]
then
    usage
    exit
fi

case "$1" in
    basic)
        cd ..
        docker build -t attractors:latest -f docker/Dockerfile.basic .
        ;;
    hugo)
        cd ..
        docker build -t attractors:latest -f docker/Dockerfile.hugo .
        ;;
    *)
        usage
        exit
        ;;
esac
