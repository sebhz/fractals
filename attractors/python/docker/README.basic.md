# Having fun with containers
Containers are in fashion these days, so let's follow the hype !

## Build the basic container to generate one attractor each day
This will create the attractor generator docker image.
By default one attractor will be generated each day at midnight (`run.sh 00:00:00`).

```
% cd docker
% ./docker_build.sh basic
```

## [OPTIONAL] Create an empty docker volume
We'll be using it to store all the web pages that our attractor generator
will create. Since it is empty, it will be populated by the default content
of the generator html directory (css, js, icons...) when first mounted.
You can also skip this step as a new volume will be created during the next step
if it does not exist.
```
% docker volume create attractors-data
```

## Launch the attractor generator container
It is important to do this first, so that our empty volume is populated by the
default content of the attractor generator html directory.

The machine can either run in oneshot mode (the default), for use with cron, or
run in continuous mode, where it will generate one attractor per day at the specified
time.

To run in continuous mode, generating one attractor each day at 6:00AM:

```
% docker run --rm \
             --detach \
             --mount source=attractors-data,target=/opt/attractors/html \
             --name attractors-machine \
             attractors:latest continuous 06:00:00
```

## Launch the attractor web page generator
We use a plain nginx image to expose our beautiful attractors to the world.
Since our volume is not empty anymore, it will obscure the standard nginx content.
```
% docker run --rm \
             --detach \
             --mount source=attractors-data,target=/usr/share/nginx/html,readonly \
             --publish 8080:80 \
             --name attractors-web \
             nginx:latest
```

The web pages will be accessible from the host on port 8080 (--publish option).

