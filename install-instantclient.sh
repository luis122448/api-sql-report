#!/bin/bash
unzip -n ./oracle_home/instantclient-basic-linux.x64-23.8.0.25.04.zip -d /opt/oracle_home
unzip -n ./oracle_home/instantclient-sqlplus-linux.x64-23.8.0.25.04.zip -d /opt/oracle_home
unzip -n ./oracle_home/instantclient-tools-linux.x64-23.8.0.25.04.zip -d /opt/oracle_home
mv ./oracle_home/instantclient_23_8 /opt/oracle_home/instantclient
cp ./app/wallet/sqlnet.ora /opt/oracle_home/instantclient/network/admin
cp ./app/wallet/tnsnames.ora /opt/oracle_home/instantclient/network/admin
cp ./app/wallet/cwallet.sso /opt/oracle_home/instantclient/network/admin

# Only for debugging purposes
# export DPI_DEBUG_LEVEL=64