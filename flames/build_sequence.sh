#!/bin/bash
set -ex

WORK_DIR="${WORK_DIR:-$(dirname $0)}"
TMP_DIR="${WORK_DIR}/tmp"
TMP_PFX=seq.
N_CTRL_PTS="${N_CTRL_PTS:-8}"
POINT_XML=points.flam3
SEQ_XML=sequence.flam3
FPS="${FPS:-15}" # FPS for video sequence
LOOP="${LOOP:-1}" # End the sequence with the start image.

if [ -e /usr/bin/nproc ]; then
    nprocs=$(/usr/bin/nproc)
else
    nprocs=$(cat /proc/cpuinfo 2>/dev/null | egrep '^processor' | wc -l)
fi
N_THREADS="${N_THREADS:-$nprocs}"

PREFIX="${TMP_DIR}/${TMP_PFX}"

mkdir -p "${TMP_DIR}"
rm -f "${TMP_DIR}/*"

env template="${WORK_DIR}/vidres.flam3" repeat="${N_CTRL_PTS}" flam3-genome > "${POINT_XML}"
if [ "$LOOP" == 1 ]; then
    ${WORK_DIR}/replicate_first_flame.py ${POINT_XML}
    mv /tmp/new_points.xml ${POINT_XML}
fi

env sequence=${POINT_XML} nframes=60 flam3-genome | tee ${SEQ_XML} | env nthreads=${N_THREADS} prefix=${PREFIX} verbose=1 flam3-animate

ffmpeg -framerate ${FPS} -i ${PREFIX}%05d.png -pix_fmt yuv420p -crf 22 -vcodec libx264 ${PREFIX}mp4

cp ${PREFIX}mp4 /tmp
