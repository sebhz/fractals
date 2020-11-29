FROM debian:10

RUN apt update
RUN apt install -y python3 python3-opencv python3-jinja2 imagemagick cron

RUN mkdir -p /opt/attractors
COPY attractor /opt/attractors/attractor
COPY web /opt/attractors/web

COPY docker/run.sh /opt/attractors/web/run.sh
COPY docker/attractors.cron /etc/cron.d/attractors.cron
RUN chmod 0644 /etc/cron.d/attractors.cron
RUN crontab /etc/cron.d/attractors.cron
RUN touch /var/log/attractors.log

CMD cron && tail -f /var/log/attractors.log

