FROM python:3.6-slim
LABEL maintainer="pnak"

ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux
ARG av_key
ENV av_key=$av_key

RUN set -ex \
    && buildDeps=' \
        freetds-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        git \
    ' \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
	sqlite3 \
	libsqlite3-dev \
	cron \
	vim \
    && apt-get purge --auto-remove -yqq $buildDeps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean 

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

RUN /bin/bash ./scripts/db_creation.sh 

ENTRYPOINT ["python"]
CMD ["plot.py"]
