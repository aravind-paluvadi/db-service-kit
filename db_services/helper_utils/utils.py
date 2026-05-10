"""Helper module for project, contains utility functions"""
# Standard Library Imports
import logging


# PIP Imports
from psycopg2 import OperationalError as PG_OperationalError, InterfaceError as PG_InterfaceError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
    before_sleep_log
)

# Local Imports
from .variables import (
    MAX_RETRY_ATTEMPTS,
    MIN_WAIT_SECONDS,
    MAX_WAIT_SECONDS,
    DB_REDSHIFT_RETRYABLE_ERROR_CODES
)


logger = logging.getLogger(__name__)


def db_retryable(logger_instance: logging.Logger):
    """
    Standard database retryable function that can be used to retry database operations in case of transient errors.
    It uses the tenacity library to implement the retry logic, which includes exponential backoff with jitter and
    logging of retry attempts. The retry logic is specifically designed to handle transient psycopg2 errors that are
    commonly encountered when working with PostgreSQL databases, such as connection issues or operational errors.

    Parameters:
    ----------
        logger_instance:
                A logging.Logger instance that will be used to log retry attempts. The logger will log a warning message
                each time a retry is attempted due to a transient database error.
    Returns:
    -------
    """
    return retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential_jitter(initial=MIN_WAIT_SECONDS, max=MAX_WAIT_SECONDS),
        before_sleep=before_sleep_log(logger_instance, logging.WARNING),  # type: ignore[arg-type]
        retry=retry_if_exception(_is_retryable_db_error),
        reraise=True
    )


def _is_retryable_db_error(exception: BaseException) -> bool:
    """Return True if exception is transient psycopg2 error and should be retried."""
    if isinstance(exception,  PG_InterfaceError):
        return True
    if isinstance(exception, PG_OperationalError):
        code = getattr(exception, "pgcode", None)
        if code is None:
            return True
        return code in DB_REDSHIFT_RETRYABLE_ERROR_CODES
    return False
