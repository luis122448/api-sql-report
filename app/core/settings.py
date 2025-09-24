import os
from datetime import datetime
import pytz

# Read the timezone from an environment variable, defaulting to 'UTC'
# This makes the application's timezone configurable.
APP_TIMEZONE_STR = os.environ.get("APP_TIMEZONE", "UTC")

# Create a pytz timezone object for use throughout the application
try:
    APP_TIMEZONE = pytz.timezone(APP_TIMEZONE_STR)
except pytz.UnknownTimeZoneError:
    print(f"Warning: Unknown timezone '{APP_TIMEZONE_STR}' from environment. Defaulting to UTC.")
    APP_TIMEZONE_STR = "UTC"
    APP_TIMEZONE = pytz.timezone(APP_TIMEZONE_STR)

def get_oracle_timezone_offset() -> str:
    """
    Returns the current UTC offset for the configured timezone
    in a format suitable for Oracle's 'ALTER SESSION SET TIME_ZONE'.
    e.g., '-05:00' or '+01:00'.
    """
    now = datetime.now(APP_TIMEZONE)
    offset = now.utcoffset()
    if offset is None:
        # Should only happen for UTC if it doesn't have a specific offset in some contexts
        return "+00:00"
    
    total_seconds = offset.total_seconds()
    hours = int(total_seconds / 3600)
    minutes = int(abs(total_seconds % 3600) / 60)
    
    return f"{hours:+03d}:{minutes:02d}"

ORACLE_TIMEZONE_OFFSET = get_oracle_timezone_offset()
