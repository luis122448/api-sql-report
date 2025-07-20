FROM python:3.11.12-slim
LABEL maintainer="luis122448"

WORKDIR /opt

COPY ./requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip && \
    rm -rf /var/lib/apt/lists/*

COPY ./app /opt/app/
COPY ./oracle_home/*.zip /opt/oracle_home/
COPY ./oracle_home/build-install-instantclient.sh /opt/install-instantclient.sh
RUN chmod +x /opt/install-instantclient.sh
RUN mkdir -p /opt/database
RUN apt-get update && apt-get install -y libaio1

ENV LD_LIBRARY_PATH=/opt/oracle_home/instantclient
ENV ORACLE_HOME=/opt/oracle_home/instantclient

# RUN /bin/bash -c "/opt/install-instantclient.sh"
# RUN ls -l /opt/oracle_home/instantclient

COPY ./entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

EXPOSE 8001
CMD ["/opt/entrypoint.sh"]