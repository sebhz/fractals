FROM debian:10

RUN apt update
RUN apt install -y python3 python3-opencv python3-jinja2 cron

RUN mkdir -p /opt/attractors
RUN mkdir -p /opt/attractors/html
COPY attractor /opt/attractors/attractor
COPY web /opt/attractors/web
COPY web/css /opt/attractors/html/css
COPY web/icons /opt/attractors/html/icons
COPY web/js /opt/attractors/html/js

COPY docker/run.sh /opt/attractors/web/run.sh
COPY docker/attractors.cron /etc/cron.d/attractors.cron
RUN chmod 0744 /opt/attractors/web/run.sh
RUN chmod 0644 /etc/cron.d/attractors.cron
RUN crontab /etc/cron.d/attractors.cron
RUN touch /var/log/attractors.log

CMD cron && tail -f /var/log/attractors.log

