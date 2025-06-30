#!/bin/bash
ARCH=$(uname -m)
VERSION="23.8.0.25.04" # Define version for easier updates

if [ "$ARCH" = "x86_64" ]; then
    BASIC_ZIP="instantclient-basic-linux.x64-${VERSION}.zip"
    SQLPLUS_ZIP="instantclient-sqlplus-linux.x64-${VERSION}.zip"
    TOOLS_ZIP="instantclient-tools-linux.x64-${VERSION}.zip"
    SDK_ZIP="instantclient-sdk-linux.x64-${VERSION}.zip"
elif [ "$ARCH" = "aarch64" ]; then
    BASIC_ZIP="instantclient-basic-linux.arm64-${VERSION}.zip"
    SQLPLUS_ZIP="instantclient-sqlplus-linux.arm64-${VERSION}.zip"
    TOOLS_ZIP="instantclient-tools-linux.arm64-${VERSION}.zip"
    SDK_ZIP="instantclient-sdk-linux.arm64-${VERSION}.zip"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

unzip -n "./oracle_home/$BASIC_ZIP" -d /opt/oracle_home
unzip -n "./oracle_home/$SQLPLUS_ZIP" -d /opt/oracle_home
unzip -n "./oracle_home/$TOOLS_ZIP" -d /opt/oracle_home
unzip -n "./oracle_home/$SDK_ZIP" -d /opt/oracle_home

mv ./oracle_home/instantclient_23_8 /opt/oracle_home/instantclient
cp ./app/wallet/sqlnet.ora /opt/oracle_home/instantclient/network/admin
cp ./app/wallet/tnsnames.ora /opt/oracle_home/instantclient/network/admin
cp ./app/wallet/cwallet.sso /opt/oracle_home/instantclient/network/admin

# Only for debugging purposes
export DPI_DEBUG_LEVEL=64