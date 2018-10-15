FROM python:3.6-stretch
MAINTAINER osslabs <code@openslatedata.com>

# Install Docker client
ENV DOCKERVERSION=17.09.1-ce
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
    && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 \
    -C /usr/local/bin docker/docker \
    && rm docker-${DOCKERVERSION}.tgz

ARG DOCKER_GID=999
RUN groupadd -for -g ${DOCKER_GID} docker \
    && usermod -a -G docker root

ENV SRC_DIR /usr/local/src
WORKDIR ${SRC_DIR}

RUN mkdir ${SRC_DIR}/results

COPY files/ /
RUN chmod +x /usr/local/bin/*

RUN pip3 install pipenv

COPY ./ ${SRC_DIR}/

RUN pipenv install --system --dev && \
    rm -rf /root/.cache/pip

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
