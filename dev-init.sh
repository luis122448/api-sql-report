#!/bin/bash

# Environment Variables
# var/www/api-sql-reports/data-ingestor-python/py-etl-oracle
export DPI_DEBUG_LEVEL=64
export TNS_ADMIN=var/www/api-sql-reports/data-ingestor-python/app/wallet
export LD_LIBRARY_PATH=var/www/api-sql-reports/data-ingestor-python/oracle_home/instantclient
export PATH=var/www/api-sql-reports/data-ingestor-python/oracle_home/instantclient:$PATH

# Exporting environment variables
source ~/.bashrc

# Restar Virtual Environment
deactivate
source .venv/bin/activate

# Start server
python app/server.py
