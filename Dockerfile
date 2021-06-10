FROM docker.io/python:3.8-alpine
LABEL maintainer="Vladislav Yarmak <vladislav-ex-src@vm-0.com>"

COPY . /build
WORKDIR /build
RUN true \
   && apk add --no-cache --virtual .build-deps alpine-sdk libffi-dev \
   && apk add --no-cache libffi \
   && pip3 install --no-cache-dir . \
   && apk del .build-deps \
   && mkdir -p /usr/local/bin \
   && install docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh \
   && true

VOLUME [ "/certs" ]
EXPOSE 1940/tcp 8080/tcp
ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]
