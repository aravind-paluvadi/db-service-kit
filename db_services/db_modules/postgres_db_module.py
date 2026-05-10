"""File to handle the Postgres db module"""
# Standard Library Imports
import logging
from threading import Lock
from contextlib import contextmanager
from typing import Optional, List, Tuple, Dict

# Pip Imports
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, execute_batch


# Local Imports
from db_services.helper_utils.utils import db_retryable


logger = logging.getLogger(__name__)

__all__ = ["PostgresDBModule"]


class PostgresDBModule:
    """
    Class to handle the Postgres SQL db module.

    Features:
        - Connection pooling (thread-safe)
        - Automatic retry on transient errors
        - Context-managed connections and cursors
        - Parameterized queries (SQL injection safe)
        - Lazy pool initialization
    """

    def __init__(
            self,
            host: str,
            dbname: str,
            user: str,
            password: str,
            port: int = 5439,
            ssl_mode: str = "require",
            min_connections: int = 1,
            max_connections: int = 10,
            connect_timeout: int = 10
    ) -> None:
        """
        Parameters:
        ----------
            host:
                Host for the Postgres database
            dbname:
                Database name
            user:
                Username for authentication
            password:
                Password for authentication
            port:
                Port number (default: 5439)
            ssl_mode:
                SSL mode for secure connection (default: "require")
            min_connections:
                Minimum number of connections in the pool (default: 1)
            max_connections:
                Maximum number of connections in the pool (default: 10)
            connect_timeout:
                Connection timeout in seconds (default: 10)
        """
        self._dns_params = {
            "host": host,
            "dbname": dbname,
            "user": user,
            "password": password,
            "port": port,
            "sslmode": ssl_mode,
            "connect_timeout": connect_timeout
        }
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._pool: Optional[ThreadedConnectionPool] = None
        self._pool_lock = Lock()

    # --------------------Pool Management----------------------------
    @property
    def initialize_pool(self) -> ThreadedConnectionPool | None:
        """Lazy initialize the connection pool for the first use, thread-safe"""
        if self._pool is None or self._pool.closed:
            with self._pool_lock:
                if self._pool is None or self._pool.closed:  # Double-check after acquiring lock
                    logger.info("Initializing Postgres connection pool (max=%d)", self._max_connections)
                    self._pool = ThreadedConnectionPool(
                        minconn=self._min_connections,
                        maxconn=self._max_connections,
                        **self._dns_params
                    )
        return self._pool

    def close(self) -> None:
        """Close the connection pool for all the connections, thread-safe"""
        if self._pool and not self._pool.closed:
            self._pool.closeall()
            logger.info("Postgres connection pool is closed")

    # ------------------ Context Managed Connections --------------------------------------------------

    @contextmanager
    def _connection(self, autocommit: bool = False):
        """
        Yields a connection from the pool.
        Parameters:
        ----------
            autocommit:
                Whether to enable autocommit mode for the connection (default: False)
        Return:
        ------
            Context-managed connection from the pool
        """
        connection = self.initialize_pool.getconn()
        close_connection = False
        try:
            connection.autocommit = autocommit
            yield connection
            if not autocommit:
                connection.commit()
        except Exception:
            close_connection = True
            if not autocommit:
                try:
                    connection.rollback()
                except Exception:
                    logger.warning("Rollback failed", exc_info=True)
            raise
        finally:
            self.initialize_pool.putconn(connection, close=close_connection)


    @contextmanager
    def _cursor(self, autocommit: bool = False):
        """
        Yields a cursor from a connection in the pool with proper cleanup.
        Parameters:
        ----------
        autocommit:
            Whether to enable autocommit mode for the connection (default: False)
        Return:
        ------
            Context-managed cursor from a connection in the pool
        """
        with self._connection(autocommit=autocommit) as connection:
            cursor = connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    # ------------------ Query Execution --------------------------------------------------
    @db_retryable(logger)
    def execute(self, query: str, params: Optional[Tuple] = None, autocommit: bool = False) -> None:
        """
        Execute a non-returning query (INSERT, UPDATE, DELETE, DDL, UNLOAD, etc.).
        Parameters:
        ----------
            query:
                SQL query to execute (parameterized with %s placeholders)
            params:
                Optional tuple of parameters to pass to the query (for parameterized queries)
            autocommit:
                Whether to enable autocommit mode for this query (default: False). Set True
                for DDL or COPY/UNLOAD commands.
        """
        logger.info("Executing statement: (autocommit=%s)", autocommit)
        logger.debug("Query: %.200s", query)
        with self._cursor(autocommit=autocommit) as cursor:
            cursor.execute(query, params)

    @db_retryable(logger)
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a SELECT and return all rows
        Parameters:
        ----------
            query:
                SQL query to execute (parameterized with %s placeholders)
            params:
                Optional tuple of parameters to pass to the query (for parameterized queries)

        Returns:
        -------
            List of tuples representing the rows returned by the query
        """
        logger.info("Executing fetchall query")
        logger.debug("Query: %.200s", query)
        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    @db_retryable(logger)
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """
        Execute a SELECT and return the first row or None.
        Parameters:
        ----------
            query:
                SQL query to execute (parameterized with %s placeholders)
            params:
                Optional tuple of parameters to pass to the query (for parameterized queries)

        Returns:
        -------
            A single tuple representing the first row returned by the query, or None if no rows are returned
        """
        logger.info("Executing fetchone query")
        logger.debug("Query: %.200s", query)
        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    @db_retryable(logger)
    def fetch_all_as_dict(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Execute a SELECT and return all rows as a list of dictionaries (column names as keys).
        Parameters:
        ----------
            query:
                SQL query to execute (parameterized with %s placeholders)
            params:
                Optional tuple of parameters to pass to the query (for parameterized queries)

        Returns:
        -------
            List of dictionaries representing the rows returned by the query, with column names as keys
        """
        logger.info("Executing fetchall query")
        logger.debug("Query: %.200s", query)
        with self._connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    @db_retryable(logger)
    def execute_batch(self, query: str, data: List[Tuple], page_size: int = 1000) -> None:
        """
        Efficiently execute a batch of parameterized queries using psycopg2's execute_batch
        for better performance.
        Parameters:
        ----------
            query:
                SQL query to execute (parameterized with %s placeholders)
            params_list:
                List of tuples, where each tuple contains the parameters for one execution of the query
            page_size:
                Number of records to execute in each batch (default: 1000)
        """
        logger.info("Executing batch statement with %d records (page_size=%d)", len(data), page_size)
        logger.debug("Query: %.200s", query)
        with self._cursor() as cursor:
            execute_batch(cursor, query, data, page_size=page_size)

    # ------------------------- Convenience --------------------------------------------------------

    @classmethod
    def from_secrets(cls, secrets: dict, **kwargs) -> "PostgresDBModule":
        """
        Factory method to create PostgresDBModule instance from a secrets dictionary (e.g. from AWS Secrets Manager)
        Expected keys in secrets dict: host, dbname, username, password, port (optional)
        Parameters:
        ----------
            secrets:
                Name of the secret in AWS Secrets Manager
            kwargs:
                Additional parameters to pass to the constructor (e.g. connection pool settings)
        Returns:
        -------
            PostgresDBModule instance
        """
        return cls(
            host=secrets["host"],
            dbname=secrets["dbname"],
            user=secrets["username"],
            password=secrets["password"],
            port=int(secrets.get("port", 5439)),
            **kwargs
        )

    def __repr__(self) -> str:
        """
        Returns:
        -------
            String representation of the PostgresDBModule instance, showing connection parameters
            (excluding password for security).
        """
        return (
            f"PostgresDBModule(host={self._dns_params['host']!r}, "
            f"db_name={self._dns_params['dbname']!r}, "
            f"user={self._dns_params['user']!r}, "
            f"port={self._dns_params['port']})"
        )

    def __enter__(self):
        """
        Context manager entry method to allow using PostgresDBModule in a with block.

        Returns:
        -------
            self: The PostgresDBModule instance itself, allowing users to use it within the with block.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """"
        Context manager exit method to ensure the connection pool is closed when exiting a with block.
        Parameters:
        ----------
            exc_type:
                Exception type if an exception was raised, otherwise None
            exc_val:
                Exception value if an exception was raised, otherwise None
            exc_tb:
                Exception traceback if an exception was raised, otherwise None

        Returns:
        -------
            False to indicate that exceptions should not be suppressed (if any were raised)
        """
        self.close()
        return False
