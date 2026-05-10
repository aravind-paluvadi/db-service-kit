"""Shared constants for utilities and other task modules"""

MAX_RETRY_ATTEMPTS = 3
MIN_WAIT_SECONDS = 1
MAX_WAIT_SECONDS = 10

# Transient errors worth retrying
DB_REDSHIFT_RETRYABLE_ERROR_CODES = frozenset({
    "08000", # connection_exception
    "08001", # sqlclient_unable_to_establish_sqlconnection
    "08003", # connection_does_not_exist
    "08006", # connection_failure
    "57P01", # admin_shutdown
    "53300"  # too_many_connections
})
