# Having fun with containers
Containers are in fashion these days, so let's follow the hype !

## Build the basic container to generate one attractor each day
This will create the attractor generator docker image, installing a crontab to
generate one attractor each day.

```
% cd docker
% ./docker_build.sh hugo
```

## Launch our attractor machine

```
% docker run --rm \
             --detach  \
             --volume /opt/attractors/html:/opt/attractors/html \
             --name attractors-machine \
             attractors:latest
```

## Prepare the static web page site
We'll use [Hugo][1], with the [Autophugo][2] theme, and run Hugo inside a container
also.
To simplify things, we'll host the site on the disk directly rather than using a
Docker volume to share data between our attractor generator and Hugo.
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

Change the configuration, by editing config.toml or copying ours.

```
% cp <attractors_root>/web/hugo/config.toml .
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

[1]https://gohugo.io/
[2]https://github.com/kc0bfv/autophugo