# Do electric sheep...
A shell script to generate sequences of Scott Draves flames.

The script can be used to generate videos suitable for infinite
looping.

# Pre-requisite
This depends on [flam3](https://github.com/scottdraves/flam3) program written by Scott Draves.

# Docker
- Build a docker container to generate flames: `docker build -t flames:latest .`.
- Launch generation in the container: `docker run -v /tmp:/tmp flames:latest`. The resulting sequence will be found in `/tmp/flame.mp4`.
Check build_sequence.sh script for the list of env variables that can be passed:
    * to change number of control points or FPS: `docker run -e N_CTRL_PTS=16 -e FPS=30 -v /tmp:/tmp flames:latest`.
    * to create a non looping flame and store / use its last frame for subsequent trials: `docker run -e LOOP=0 RESTORE_FLAME=1 RESTORED_FLAME_FILE=/etc/docker/services/flames/saved_flame.xml -v /tmp:/tmp -v /etc/docker/services/flames:/etc/docker/services/flames flames:latest`.

# References
Check [Electric sheep](https://electricsheep.org/). It is worth it.
