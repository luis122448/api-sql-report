#!/bin/bash

# Environment Variables
# var/www/sql-api-reports/api-sql-report/py-etl-oracle
export DPI_DEBUG_LEVEL=64
export TNS_ADMIN=/var/www/sql-api-reports/api-sql-report/app/keys
export LD_LIBRARY_PATH=/var/www/sql-api-reports/api-sql-report/oracle_home/instantclient
export PATH=/var/www/sql-api-reports/api-sql-report/oracle_home/instantclient:$PATH

# Start server
python app/server.py
