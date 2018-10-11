FROM python:3.6-stretch
MAINTAINER osslabs <code@openslatedata.com>

ENV SRC_DIR /usr/local/src
WORKDIR ${SRC_DIR}

RUN mkdir ${SRC_DIR}/results

RUN pip3 install pipenv

COPY ./ ${SRC_DIR}/

RUN pipenv install --system --dev && \
    rm -rf /root/.cache/pip

RUN chmod +x /usr/local/bin/*

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["/bin/bash"]
