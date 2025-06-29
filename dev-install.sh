#!/bin/bash
# Install Python 3.12
sudo apt install python3.12 -y
sudo apt install python3.12-venv

# Create a virtual environment
python3 -m venv .venv

# Exporting environment variables
source .venv/bin/activate

# Install dependencies
sudo apt-get update
sudo apt-get install -y libffi-dev python3-dev gcc
sudo apt install libaio1t64
sudo apt install alien

# Create symbolic link
sudo ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1

source .venv/bin/activate
# Install dependencies
pip install -r requirements.txt