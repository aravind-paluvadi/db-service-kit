"""Tests file for Postgres DB Module"""
# PIP Imports
import pytest
from psycopg2 import ProgrammingError
from psycopg2.extras import RealDictCursor

# Local Imports
from db_services.db_modules import PostgresDBModule


class TestPostgresDBModule:
    """Test class for Postgres DB Module"""

    def test_execute(self, client, mock_initialize_pool):
        """Test execute method for Postgres DB Module"""
        _, mock_connection, mock_cursor = mock_initialize_pool

        client.execute("INSERT INTO table_name VALUES (%s)", params=("value",))
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO table_name VALUES (%s)", ("value",)
        )
        mock_connection.commit.assert_called_once()

    def test_execute_autocommit(self, client, mock_initialize_pool):
        """Test execute method with autocommit=True does not call commit for Postgres DB Module"""
        _, mock_connection, mock_cursor = mock_initialize_pool

        client.execute("CREATE TABLE table_name (id INT)", autocommit=True)
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_not_called()

    def test_execute_roll_back_on_error(self, client, mock_initialize_pool):
        """Test _connection rolls back and discards connection on error for Postgres DB Module"""
        _, mock_connection, mock_cursor = mock_initialize_pool
        mock_cursor.execute.side_effect = ProgrammingError("Syntax Error")

        with pytest.raises(ProgrammingError):
            client.execute("SELECT 1")

        mock_connection.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        # putconn called with close=True to discard broken connection
        mock_initialize_pool[0].putconn.assert_called_once_with(mock_connection, close=True)

    def test_execute_putconn_clase_false_on_success(self, client, mock_initialize_pool):
        """Test _connection is returned to pool with close=False on success for Postgres DB Module"""
        mock_pool_obj, mock_connection, _ = mock_initialize_pool

        client.execute("INSERT INTO t VALUES (1)")

        mock_connection.commit.assert_called_once()
        mock_pool_obj.putconn.assert_called_once_with(mock_connection, close=False)

    def test_fetch_all(self, client, mock_initialize_pool):
        """Test for fetch_all method that return all rows in Postgres DB Module"""
        _, _, mock_cursor = mock_initialize_pool
        mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

        result = client.fetch_all("SELECT * FROM table_name")

        assert result == [("row1",), ("row2",)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table_name", None)

    def test_execute_no_params(self, client, mock_initialize_pool):
        """Test execute method with no params for Postgres DB Module"""
        _, mock_connection, mock_cursor = mock_initialize_pool

        client.execute("DELETE FROM table_name")

        mock_cursor.execute.assert_called_once_with("DELETE FROM table_name", None)
        mock_connection.commit.assert_called_once()

    def test_fetch_all_with_params(self, client, mock_initialize_pool):
        """Test fetch_all passes params to cursor.execute for Postgres DB Module"""
        _, _, mock_cursor = mock_initialize_pool
        mock_cursor.fetchall.return_value = [("row1",)]

        result = client.fetch_all("SELECT * FROM table_name WHERE id = %s", params=(42,))

        assert result == [("row1",)]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table_name WHERE id = %s", (42,))

    def test_fetch_one(self, client, mock_initialize_pool):
        """Test for fetch_one method that return one row in Postgres DB Module"""
        _, _, mock_cursor = mock_initialize_pool
        mock_cursor.fetchone.return_value = ("row1",)

        result = client.fetch_one("SELECT * FROM table_name")

        assert result == ("row1",)
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table_name", None)

    def test_fetch_one_returns_none(self, client, mock_initialize_pool):
        """Test fetch_one returns None when no rows are found in Postgres DB Module"""
        _, _, mock_cursor = mock_initialize_pool
        mock_cursor.fetchone.return_value = None

        result = client.fetch_one("SELECT * FROM table_name WHERE id = %s", params=(999,))

        assert result is None
        mock_cursor.execute.assert_called_once_with("SELECT * FROM table_name WHERE id = %s", (999,))

    def test_fetch_all_as_dict(self, mocker, client, mock_initialize_pool):
        """Test fetch_all_as_dict returns list of dicts in Postgres DB Module"""
        _, mock_connection, _ = mock_initialize_pool
        mock_dict_cursor = mocker.MagicMock()
        mock_dict_cursor.fetchall.return_value = [{"col": "val"}]

        mock_cm = mocker.MagicMock()
        mock_cm.__enter__ = mocker.MagicMock(return_value=mock_dict_cursor)
        mock_cm.__exit__ = mocker.MagicMock(return_value=False)
        mock_connection.cursor.return_value = mock_cm

        result = client.fetch_all_as_dict("SELECT * FROM table_name")

        assert result == [{"col": "val"}]
        mock_dict_cursor.execute.assert_called_once_with("SELECT * FROM table_name", None)
        mock_connection.commit.assert_called_once()
        mock_connection.cursor.assert_called_once_with(cursor_factory=RealDictCursor)

    def test_execute_batch(self, mocker, client, mock_initialize_pool):
        """Test execute_batch method that return a batch of rows in Postgres DB Module"""
        _, _, mock_cursor = mock_initialize_pool
        mock_execute_batch = mocker.patch("db_services.db_modules.postgres_db_module.execute_batch")

        data = [("v1", "v2"), ("v3", "v4")]
        client.execute_batch("INSERT INTO table_name VALUES (%s, %s)", data)

        mock_execute_batch.assert_called_once_with(
            mock_cursor, "INSERT INTO table_name VALUES (%s, %s)", data, page_size=1000
        )

    def test_execute_batch_custom_page_size(self, mocker, client, mock_initialize_pool):
        """Test execute_batch method with custom page size in Postgres DB Module"""
        mock_execute_batch = mocker.patch("db_services.db_modules.postgres_db_module.execute_batch")

        data = [("v1",)]
        client.execute_batch("INSERT INTO table_name VALUES (%s)", data, page_size=500)

        mock_execute_batch.assert_called_once_with(
            mocker.ANY, "INSERT INTO table_name VALUES (%s)", data, page_size=500
        )

    def test_from_secrets(self):
        """Test from_secrets method that returns Postgres DB Module client correctly"""
        secrets = {
            "host": "myhost", "dbname": "mydb", "username": "myuser", "password": "mypass", "port": "5439"
        }

        client = PostgresDBModule.from_secrets(secrets)
        assert client._dns_params["host"] == "myhost"
        assert client._dns_params["dbname"] == "mydb"
        assert client._dns_params["user"] == "myuser"
        assert client._dns_params["port"] == 5439

    def test_from_secrets_default_port(self):
        """Test from_secrets method uses default port 5432 when not provided for Postgres DB Module"""
        secrets = {
            "host": "h", "dbname": "d", "username": "u", "password": "p"
        }

        client = PostgresDBModule.from_secrets(secrets)
        assert client._dns_params["port"] == 5439

    def test_from_secrets_raises_on_missing_key(self):
        """Test from secrets method raises KeyError when required keys are missing for Postgres DB Module"""
        with pytest.raises(KeyError):
            PostgresDBModule.from_secrets({"host": "h", "dbname": "d"})

    def test_repr_masks_password(self):
        """
        Test __repr__ method does not expose password but shows host, dbname, user and port that returns string
        representation of Postgres DB Module
        """
        client = PostgresDBModule("myhost", "mydb", "myuser", "supersecret")
        r = repr(client)

        assert "supersecret" not in r
        assert "myhost" in r
        assert "mydb" in r
        assert "myuser" in r
        assert "5439" in r

    def test_close_closes_pool(self, mocker, client):
        """Test close method that closes all the connection pool for Postgres DB Module"""
        mock_pool_obj = mocker.MagicMock()
        mock_pool_obj.closed = False
        client._pool = mock_pool_obj

        client.close()

        mock_pool_obj.closeall.assert_called_once()

    def test_close_does_nothing_when_already_ckise(self, mocker, client):
        """Test close method does not raise if pool is already closed for Postgres DB Module"""
        mock_pool_obj = mocker.MagicMock()
        mock_pool_obj.closed = True
        client._pool = mock_pool_obj

        client.close()

        mock_pool_obj.closeall.assert_not_called()

    def test_close_does_nothing_when_pool_none(self, client):
        """Test close method is safe when pool was never initialized for Postgres DB Module"""
        client._pool = None
        client.close()

    def test_context_manger_closes_pool(self, mocker):
        """Test context manager closes pool on exit for Postgres DB Module"""
        mock_close = mocker.patch.object(PostgresDBModule, "close")
        with PostgresDBModule("host", "dbname", "user", "password") as c:
            assert c is not None
        mock_close.assert_called_once()
