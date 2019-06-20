FROM python:3.6-stretch
MAINTAINER osslabs <code@openslatedata.com>

ARG user=swarmclient
ARG group=swarmclient
ARG uid=1000
ARG gid=1000

ENV HOME /home/${user}

RUN groupadd -g ${gid} ${group} \
 && useradd -c "Jenkins Slave user" -d "$HOME" -u ${uid} -g ${gid} -m -s /bin/bash ${user} \
 && chown -R ${user}:${group} $HOME \
 && chmod -R 770 $HOME

# Install Docker client
ENV DOCKERVERSION="18.09.5"
ENV DOCKER_SHA="ac485ffe7ea3f43974c4613d5142eae7ec67a611"
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz \
 && echo "$DOCKER_SHA docker-${DOCKERVERSION}.tgz" | sha1sum -c - \
 && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 \
    -C /usr/local/bin docker/docker \
 && rm docker-${DOCKERVERSION}.tgz

ARG DOCKER_GID=999
RUN groupadd -for -g ${DOCKER_GID} docker \
 && usermod -a -G docker,staff ${user}

# Install kubectl
ENV KUBE_LATEST_VERSION="v1.13.0"
ENV KUBE_SHA="5c619006fa45afce6efc51db819aff7d5ba7ef0e"
RUN curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBE_LATEST_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
 && echo "$KUBE_SHA /usr/local/bin/kubectl" | sha1sum -c - \
 && chmod +x /usr/local/bin/kubectl

# Install Rancher CLI
ENV RANCHER_VERSION="v2.2.0"
ENV RANCHER_SHA="dcd076643b39891b9f0a8c7da746ee73e0d9735c"
RUN curl -fsSLO https://github.com/rancher/cli/releases/download/${RANCHER_VERSION}/rancher-linux-amd64-${RANCHER_VERSION}.tar.gz \
 && echo "$RANCHER_SHA rancher-linux-amd64-${RANCHER_VERSION}.tar.gz" | sha1sum -c - \
 && tar xzvf rancher-linux-amd64-${RANCHER_VERSION}.tar.gz --strip 2 \
    -C /usr/local/bin \
 && rm rancher-linux-amd64-${RANCHER_VERSION}.tar.gz

# Install Helm client
ENV HELM_VERSION="v2.11.0"
ENV HELM_SHA="70fbc46e40bb3e564e91f438f9b644532b0dfcad"
RUN curl -fsSLO https://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz \
 && echo "$HELM_SHA helm-${HELM_VERSION}-linux-amd64.tar.gz" | sha1sum -c - \
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

RUN chown -R ${user}:${group} ${HOME} ${SRC_DIR}

USER ${user}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
