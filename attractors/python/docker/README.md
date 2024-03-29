# Having fun with containers
Containers are in fashion these days, so let's follow the hype !

## Build the basic container to generate one attractor each day
This will create the attractor generator docker image.
By default if the container is launched without command it will generate an attractor for the current day, then exit (`run.sh oneshot`).

```
% docker build -t attractors:latest -f docker/Dockerfile .
```

## Launch our attractor machine
The machine can either run in oneshot mode (the default), for use with cron, or
run in continuous mode, where it will generate one attractor per day at the specified
time.
In oneshot mode, one can pass a date (YYYY-MM-DD format) as parameter, to generate an
attractor for the required date. If no date is passed, the attractor is generated for the current day.

To run in continuous mode, generating one attractor each day at 6:00AM:

```
% docker run --rm \
             --detach  \
             --volume /opt/attractors/html:/opt/attractors/html \
             --name attractors-machine \
             attractors:latest continuous 06:00:00
```

To run in oneshot mode, generating one attractor for 2021 October 3rd:

```
% docker run --rm \
             --detach  \
             --volume /opt/attractors/html:/opt/attractors/html \
             --name attractors-machine \
             attractors:latest oneshot 2021-10-03
```

## Prepare the static web page site
We'll use [Hugo](https://gohugo.io/), with the [Autophugo](https://github.com/kc0bfv/autophugo) theme, and run Hugo inside a container
also.

```
% docker run --rm \
             --interactive \
             --tty \
             --volume /opt/attractors:/src \
             klakegg/hugo:asciidoctor \
             shell

hugo:/src$ hugo new site html
hugo:/src$ exit
```

Then download install the theme (from outside the container, since it does not have git
and there is no point installing it there)

```
% cd /opt/attractors
% sudo chown -R <my_id>:<my_group> html
% cd html
% git init
% git submodule add https://github.com/kc0bfv/autophugo.git themes/autophugo
```

Change the configuration, by editing config.toml or copying ours, then add
a couple of static assets

```
% cp <attractors_root>/web/config.toml .
% cp <attractors_root>/web/icons/favicon-16x16.png static
```

## Launch the attractor web page server
Since we use hugo to create our magnificent web site, let's make it really simple and use
hugo server... still in a container.
```
% docker run --rm \
             --detach \
             --volume /opt/attractors/html:/src \
             --publish 8080:8080 \ 
             --name attractors-web \
             --interactive \
             --tty \
             klakegg/hugo:asciidoctor \
             server -p8080
```

The web pages will be accessible from the host on port 8080 (--publish option).
