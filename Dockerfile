FROM python:3-slim
LABEL maintainer="Vladislav Yarmak <vladislav-ex-src@vm-0.com>"

COPY . /build
WORKDIR /build
RUN pip3 install --no-cache-dir .[uvloop] && \
    mkdir -p /usr/local/bin && \
    install docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

EXPOSE 1940/tcp 8080/tcp
ENTRYPOINT [ "/usr/local/bin/docker-entrypoint.sh" ]
