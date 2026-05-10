"""
Initial file with the fixtures needed for the test db utils package
"""
# Pip Imports
from pytest import fixture
from unittest.mock import PropertyMock

# Local Imports
from db_services.db_modules import PostgresDBModule


@fixture
def mock_initialize_pool(mocker):
    """Fixture that mocks the psycopg2 initialize_pool method in the PostgresDBModule class."""
    mock_cursor = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    mock_pool = mocker.MagicMock()
    mock_pool.getconn.return_value = mock_connection

    mocker.patch(
        "db_services.db_modules.postgres_db_module.PostgresDBModule.initialize_pool",
        new_callable=PropertyMock,
        return_value=mock_pool
    )
    return mock_pool, mock_connection, mock_cursor


@fixture
def client():
    return PostgresDBModule("host", "dbname", "user", "password")
