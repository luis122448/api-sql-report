#!/bin/bash

if [ ! -f "/opt/oracle_home/instantclient/libclntsh.so" ]; then
  echo "Installing Oracle Instant Client for arch: $(uname -m)"
  /opt/install-instantclient.sh
fi

exec python app/server.py
