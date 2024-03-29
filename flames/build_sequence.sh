#!/bin/bash
set -ex

WORK_DIR="${WORK_DIR:-$(dirname $0)}"
TMP_DIR="${WORK_DIR}/tmp"
TMP_PFX=flame.
N_CTRL_PTS="${N_CTRL_PTS:-8}"
POINT_XML=points.flam3
SEQ_XML=sequence.flam3
FPS="${FPS:-17}" # FPS for video sequence
LOOP="${LOOP:-1}" # End the sequence with the start image.
NFRAMES=60 # Number of frames to generate between each control point
# NFRAMES, FPS, LOOP and N_CTRL_PTS default will create a 1 minute video.
# Formula is VIDEO_TIME=((2*N_CTRL_PTS+1)*NFRAMES+1)/FPS (if LOOP=1).
# See below for details.

if [[ -e /usr/bin/nproc ]]; then
  nprocs="$(/usr/bin/nproc)"
else
  nprocs="$(cat /proc/cpuinfo 2>/dev/null | egrep '^processor' | wc -l)"
fi
N_THREADS="${N_THREADS:-$nprocs}"

PREFIX="${TMP_DIR}/${TMP_PFX}"

mkdir -p "${TMP_DIR}"
rm -f "${TMP_DIR}/*"

# Step 1: use flam3-genome to create 8 control flames, stored in an XML file
env template="${WORK_DIR}/vidres.flam3" repeat="${N_CTRL_PTS}" flam3-genome > "${POINT_XML}"

# Step 2: if a looping sequence is required, replicate the first control flame at the last position
if [ "$LOOP" == 1 ]; then
  ${WORK_DIR}/replicate_first_flame.py "${POINT_XML}"
  mv /tmp/new_points.xml "${POINT_XML}"
  N_CTRL_PTS="$((N_CTRL_PTS+1))"
fi

# Step 3: use flam3-genome again to create a sequence of flames from the previous XML (now containing 8 or 9 control flames).
# The documentation seems is incorrect: for a sequence description containing N control flames,
# the number of frames generated by flam3-genome will be: (2*N-1)*nframes + 1.
# The rationale is:
# - nframes corresponding to the rotation of flame0
# - nframes corresponding to the transition between flame0 and flame1
# - nframes corresponding to the rotation of flame1
# - ...
# - nframes corresponding to the transition between flameN-1 and flameN
# - nframes corresponding to the rotation of flameN
# - 1 last frame for flameN
#
# So for an 8 control flames sequence, with nframes=60, we will end up with 15*60+1 = 901 frames
# flam3-animate will eat the XML and generate the pictures from the flame description.
VIDEO_TIME=$(bc -l <<< "scale=2; ((2*${N_CTRL_PTS}-1)*${NFRAMES}+1)/${FPS}")
echo "Resulting video will last ${VIDEO_TIME} seconds"
env sequence="${POINT_XML}" nframes="${NFRAMES}" flam3-genome | tee "${SEQ_XML}" | env nthreads="${N_THREADS}" prefix="${PREFIX}" verbose=1 flam3-animate

# Step 4: generate a video from all the frames
ffmpeg -framerate "${FPS}" -i "${PREFIX}%05d.png" -pix_fmt yuv420p -crf 22 -vcodec libx264 "${PREFIX}mp4"

cp ${PREFIX}mp4 /tmp
