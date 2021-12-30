FROM debian:buster-slim

ENV ATT_MAIL=0
ENV ATT_MAIL_SERVER=""
ENV ATT_MAIL_FROM="strange.attractors@zyglute.fr"
ENV ATT_MAIL_TO="seb@zyglute.fr"

RUN apt update
RUN apt install -y python3 python3-pil python3-numpy python3-jinja2

RUN mkdir -p /opt/attractors

# Files necessary to attractor generation
RUN mkdir -p /opt/attractors/web
COPY attractor /opt/attractors/web/attractor
COPY web/templates /opt/attractors/web/templates
COPY web/create_daily.py /opt/attractors/web

# Our script
COPY docker/run.sh /opt/attractors/run.sh
RUN chmod 0744 /opt/attractors/run.sh
ENTRYPOINT ["/opt/attractors/run.sh"]
CMD ["oneshot"]
