import os
import logging
import oracledb
from dotenv import load_dotenv
from utils.path import BASEDIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the environment variables
load_dotenv()

DB_ORACLE_USER = os.getenv("DB_ORACLE_USER")
DB_ORACLE_PASSWORD = os.getenv("DB_ORACLE_PASSWORD")
DB_ORACLE_DSN = os.getenv("DB_ORACLE_DSN")
DB_ORACLE_POOL_MIN = int(os.getenv("DB_ORACLE_POOL_MIN", 2))
DB_ORACLE_POOL_MAX = int(os.getenv("DB_ORACLE_POOL_MAX", 5))
DB_ORACLE_POOL_INCREMENT = int(os.getenv("DB_ORACLE_POOL_INCREMENT", 1))

pool = None

def init_oracle_pool():
    global pool
    try:
        pool = oracledb.create_pool(
            user=DB_ORACLE_USER,
            password=DB_ORACLE_PASSWORD,
            dsn=DB_ORACLE_DSN,
            min=DB_ORACLE_POOL_MIN,
            max=DB_ORACLE_POOL_MAX,
            increment=DB_ORACLE_POOL_INCREMENT
        )
        logger.info("Oracle connection pool created successfully.")
    except oracledb.Error as e:
        logger.error(f"Error creating Oracle connection pool: {e}")
        raise

# Define operating system ( Windows or Linux )
if os.name == 'nt':
    # Windows
    clientFilePath = 'instantclient_21_11'
    clientFilePathReal = os.path.join(BASEDIR, clientFilePath)
    oracledb.init_oracle_client(lib_dir=clientFilePathReal)
else:
    # Linux
    # Use BASEDIR to construct the path dynamically for both local and Docker environments
    instant_client_path = os.path.join(BASEDIR, "oracle_home", "instantclient")
    oracledb.init_oracle_client(lib_dir=instant_client_path)

init_oracle_pool()

def get_oracle_connection():
    global pool
    if pool is None:
        init_oracle_pool()
    try:
        return pool.acquire()
    except oracledb.Error as e:
        logger.error(f"Error acquiring Oracle connection from pool: {e}")
        raise

def get_reconnect_oracle(oracle_connection):
    try:
        if testing_oracle_connection(oracle_connection):
            return oracle_connection
        else:
            return get_oracle_connection()
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la conexión: %s", e)
        raise
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la conexión: %s", e)
        raise
    except Exception as e:
        logger.error("Error genérico durante la conexión: %s", e)
        raise


def testing_oracle_connection(oracle_connection) -> bool:
    try:
        if oracle_connection is None:
            return False
        cursor = oracle_connection.cursor()
        cursor.execute("SELECT * FROM v$version")
        version = cursor.fetchone()[0]
        cursor.close()
        logger.info("Oracle Server Version: %s", version)
        return True
    except oracledb.DatabaseError as e:
        logger.error("Error de base de datos durante la prueba de conexión: %s", e)
        return False
    except oracledb.Error as e:
        logger.error("Error de Oracle durante la prueba de conexión: %s", e)
        return False
    except Exception as e:
        logger.error("Error genérico durante la prueba de conexión: %s", e)
        return False


class OracleTransaction:
    def __init__(self):
        self.connection = get_oracle_connection()

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()

    def __call__(self):
        return self
