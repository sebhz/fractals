# Having fun with containers
Containers are in fashion these days, so let's follow the hype !

## Build the generator container to generate one attractor each day
This will create the attractor generator docker image, installing a crontab to
generate one attractor each day.

```
% cd docker
% ./docker_build.sh
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
It is important to do this first, so that our empty container is populated by the
default content of the attractor generator html directory.
```
% docker run --rm \
             --detach  \
             --mount source=attractors-data,target=/opt/attractors/html \
             --name attractors-machine \
             attractors:latest
```

## Launch the attractor web page generator
We use a plain nginx image to expose our beautiful attractors to the world.
Since our volume is not empty anymore, it will obscure the standard nginx content.
```
% docker run --rm \
             --detach  \
             --mount source=attractors-data,target=/usr/share/nginx/html,readonly \
             --publish 8080:80 \
             --name attractors-web \
             nginx:latest
```

The web pages will be accessible from the host on port 8080 (--publish option).

