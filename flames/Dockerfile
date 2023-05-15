FROM debian:bullseye-slim

RUN apt update \
   && apt install -y libtool autoconf autotools-dev zlib1g-dev libxml2-dev libjpeg-dev libpng-dev ffmpeg git build-essential python3 bc

WORKDIR /tmp
RUN git clone https://github.com/scottdraves/flam3

WORKDIR /tmp/flam3
RUN autoreconf -f -i
RUN ./configure \
   && make \
   && make install

RUN mkdir -p /opt/flames

COPY build_sequence.sh replicate_first_flame.py vidres.flam3 /opt/flames/
RUN chmod 0744 /opt/flames/build_sequence.sh /opt/flames/replicate_first_flame.py

WORKDIR /opt/flames
ENTRYPOINT ["/opt/flames/build_sequence.sh"]

