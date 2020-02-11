#!/bin/bash

TMP_DIR=./tmp
TMP_PFX=seq.
N_CTRL_PTS=8
POINT_XML=points.flam3
SEQ_XML=sequence.flam3
FPS=15 # FPS for video sequence
LOOP=1 # End the sequence with the start image.

if [ -e /usr/bin/nproc ]; then
    nprocs=$(/usr/bin/nproc)
else
    nprocs=$(cat /proc/cpuinfo 2>/dev/null | egrep '^processor' | wc -l)
fi
N_THREADS=${nproc}

PREFIX=${TMP_DIR}/${TMP_PFX}

mkdir -p ${TMP_DIR}
rm -f ${TMP_DIR}/*

env template=vidres.flam3 repeat=${N_CTRL_PTS} flam3-genome > ${POINT_XML}
if [ "$LOOP" == 1 ]; then
    ./replicate_first_flame.py ${POINT_XML}
    mv /tmp/new_points.xml ${POINT_XML}
fi

env sequence=${POINT_XML} nframes=60 flam3-genome | tee ${SEQ_XML} | env nthreads=${N_THREADS} prefix=${PREFIX} verbose=1 flam3-animate

#ffmpeg -f image2 -r $FPS -i ${PREFIX}%05d.png -crf 22 -vcodec libx264 ${PREFIX}mp4
ffmpeg -framerate $FPS -i ${PREFIX}%05d.png -pix_fmt yuv420p -crf 22 -vcodec libx264 ${PREFIX}mp4
