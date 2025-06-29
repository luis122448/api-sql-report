FROM python:3.11.12-slim
LABEL luis122448 <luis122448@gmail.com>

WORKDIR /opt

ARG DB_ORACLE_USER
ARG DB_ORACLE_PASSWORD
ARG DB_ORACLE_DSN
ARG MINIO_URL
ARG MINIO_ACCESS_KEY
ARG MINIO_SECRET_KEY
ARG JWT_SECRET_KEY

COPY ./requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip && \
    rm -rf /var/lib/apt/lists/*

COPY ./app /opt/app/
COPY ./oracle_home /opt/oracle_home/
COPY ./backup /opt/backup/
COPY ./install-instantclient.sh /opt/install-instantclient.sh

RUN chmod +x /opt/install-instantclient.sh

ENV LD_LIBRARY_PATH=/opt/oracle_home/instantclient

RUN /bin/bash -c "/opt/install-instantclient.sh"

RUN apt-get update && apt-get install -y libaio1

EXPOSE 8001
CMD [ "python", "app/server.py" ]