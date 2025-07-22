#!/bin/bash
ARCH=${TARGETARCH:-$(uname -m)}
VERSION="23.8.0.25.04" # Define version for easier updates

echo "Detected architecture: $ARCH"

if [ "$ARCH" = "amd64" ]; then
    ARCH="x86_64"
elif [ "$ARCH" = "arm64" ]; then
    ARCH="aarch64"
fi

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

unzip -n "/opt/oracle_home/$BASIC_ZIP" -d /opt/oracle_home
unzip -n "/opt/oracle_home/$SQLPLUS_ZIP" -d /opt/oracle_home
unzip -n "/opt/oracle_home/$TOOLS_ZIP" -d /opt/oracle_home
unzip -n "/opt/oracle_home/$SDK_ZIP" -d /opt/oracle_home

rm -rf /opt/oracle_home/instantclient/*
mkdir -p /opt/oracle_home/instantclient/

mv /opt/oracle_home/instantclient_23_8/* /opt/oracle_home/instantclient/
cp /opt/app/keys/sqlnet.ora /opt/oracle_home/instantclient/network/admin
cp /opt/app/keys/tnsnames.ora /opt/oracle_home/instantclient/network/admin
cp /opt/app/keys/cwallet.sso /opt/oracle_home/instantclient/network/admin

rm -rf /opt/oracle_home/instantclient_23_8
rm -rf /opt/oracle_home/META-INF