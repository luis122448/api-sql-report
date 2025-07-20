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

unzip -n "./oracle_home/$BASIC_ZIP" -d ./oracle_home/
unzip -n "./oracle_home/$SQLPLUS_ZIP" -d ./oracle_home/
unzip -n "./oracle_home/$TOOLS_ZIP" -d ./oracle_home/
unzip -n "./oracle_home/$SDK_ZIP" -d ./oracle_home/

rm -rf ./oracle_home/instantclient/*
mkdir -p ./oracle_home/instantclient/

mv ./oracle_home/instantclient_23_8/* ./oracle_home/instantclient/
cp ./app/keys/sqlnet.ora ./oracle_home/instantclient/network/admin
cp ./app/keys/tnsnames.ora ./oracle_home/instantclient/network/admin
cp ./app/keys/cwallet.sso ./oracle_home/instantclient/network/admin

rm -rf ./oracle_home/instantclient_23_8
rm -rf ./oracle_home/META-INF

# Only for debugging purposes
export DPI_DEBUG_LEVEL=64