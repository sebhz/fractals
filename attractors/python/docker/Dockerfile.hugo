FROM debian:buster-slim

RUN apt update
RUN apt install -y python3 python3-pil python3-numpy

RUN mkdir -p /opt/attractors

# Files necessary to attractor generation
RUN mkdir -p /opt/attractors/web
COPY attractor /opt/attractors/web/attractor
COPY web/hugo/create_daily.py /opt/attractors/web

# Our script
COPY docker/run.sh /opt/attractors/run.sh
RUN chmod 0744 /opt/attractors/run.sh
ENTRYPOINT ["/opt/attractors/run.sh"]
CMD ["oneshot"]
