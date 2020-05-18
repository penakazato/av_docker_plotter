FROM python:3.6-slim
LABEL maintainer="pnak"

ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux
ENV av_key=X9RM83J85A2KGNAC

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

RUN /bin/bash db_creation.sh 
RUN python pull_data.py

ENTRYPOINT ["python"]
CMD ["plot.py"]
