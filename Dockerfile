FROM python:3.6-stretch
MAINTAINER osslabs <code@openslatedata.com>

# Install Docker client
ENV DOCKERVERSION="17.09.1-ce"
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
 && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 \
    -C /usr/local/bin docker/docker \
 && rm docker-${DOCKERVERSION}.tgz

ARG DOCKER_GID=999
RUN groupadd -for -g ${DOCKER_GID} docker \
 && usermod -a -G docker root

# Install kubectl
ENV KUBE_LATEST_VERSION="v1.11.2"

RUN curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
 && chmod +x /usr/local/bin/kubectl

# Install Rancher CLI
ENV RANCHER_VERSION="v2.0.5"
RUN curl -fsSLO https://github.com/rancher/cli/releases/download/${RANCHER_VERSION}/rancher-linux-amd64-${RANCHER_VERSION}.tar.gz \
 && tar xzvf rancher-linux-amd64-${RANCHER_VERSION}.tar.gz --strip 2 \
    -C /usr/local/bin \
 && rm rancher-linux-amd64-${RANCHER_VERSION}.tar.gz

# Install Helm client
ENV HELM_VERSION="v2.11.0"
RUN curl -fsSLO https://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz \
 && tar xzvf helm-${HELM_VERSION}-linux-amd64.tar.gz --strip 1 \
    -C /usr/local/bin \
 && chmod +x /usr/local/bin/helm \
 && rm helm-${HELM_VERSION}-linux-amd64.tar.gz

# Install compose-flow
ENV SRC_DIR /usr/local/src
WORKDIR ${SRC_DIR}

RUN mkdir ${SRC_DIR}/results

COPY files/ /
RUN chmod +x /usr/local/bin/*

RUN pip3 install pipenv

COPY Pipfile Pipfile.lock ${SRC_DIR}/

RUN pipenv install --system --dev && \
    rm -rf /root/.cache/pip

COPY ./ ${SRC_DIR}/

RUN python setup.py install

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
